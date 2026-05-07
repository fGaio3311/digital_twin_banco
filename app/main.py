import asyncio
import hashlib
import json
import logging
import os
import pathlib
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlparse

import jwt
import psutil
import psycopg2  # necessário para wait_for_postgres
import requests
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError

# ---------- Métricas Prometheus ----------
# Usar um registry separado para evitar duplicação
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, func, text, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.base import BaseHTTPMiddleware

from app.domain.twin import DigitalTwin
from app.middleware.limiter import allow

# imports locais
from app.models.models import Base, Log, Transaction, User
from app.schemas import Event
from app.services.mqtt_service import mqtt_service
from app.settings import Settings
from app.utils import process_logs_file

registry = CollectorRegistry()

PROCESS_LATENCY = Histogram(
    "dt_process_latency_seconds",
    "Tempo para aplicar um evento no Digital Twin",
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1, 2],
    registry=registry,
)
MESSAGES_PROCESSED = Counter(
    "dt_messages_processed_total",
    "Total de eventos processados pelo Digital Twin",
    registry=registry,
)
CPU_USAGE = Gauge(
    "dt_cpu_percent", "Percentual de CPU usado pelo DT", registry=registry
)
MEM_USAGE = Gauge("dt_mem_bytes", "Uso de memória RAM (RSS) pelo DT", registry=registry)

# registra o início para cálculo de uptime
START_TIME = time.time()

# arquivo de log de métricas (JSON Lines)
METRICS_LOG_PATH = pathlib.Path("metrics_log.jsonl")

TESTING = os.getenv("TESTING", "0") == "1"

settings = Settings()
settings.require_api_fields()
DATABASE_URL = settings.database_url or ""


# ---------- espera Postgres ficar disponível ----------
def wait_for_postgres(url, timeout=30):
    parsed = urlparse(url)
    user = parsed.username
    password = parsed.password
    dbname = parsed.path.lstrip("/")
    host = parsed.hostname
    port = parsed.port or 5432
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            conn.close()
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("Postgres não ficou disponível a tempo")


if DATABASE_URL.startswith("postgres"):
    wait_for_postgres(DATABASE_URL)

# ---------- FastAPI ----------
app = FastAPI(
    title=settings.title,
    description="Bank Simulator with Digital Twin",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------- Autenticação (precisa antes do middleware que decodifica token) ----------
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# ---------- registro de eventos customizados (para plotting etc) ----------
def record_event(
    endpoint: str,
    latency: float,
    success: bool,
    user: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
):
    entry: dict[str, Any] = {
        "time": datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "latency_ms": latency * 1000,
        "success": success,
        "user": user,
    }
    if extra:
        entry.update(extra)
    try:
        with METRICS_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        logging.warning(
            f"Failed to write metrics log: {e}"
        )  # não quebra a API por falha de log


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        endpoint = request.url.path
        user = None
        try:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                token = auth.split(" ", 1)[1]
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user = payload.get("sub")
        except Exception:
            user = None

        success = False
        try:
            response = await call_next(request)
            success = 200 <= response.status_code < 400
        except Exception:
            success = False
            raise
        finally:
            latency = time.time() - start
            record_event(endpoint, latency, success, user)
        return response


app.add_middleware(MetricsMiddleware)


class SecurityTelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        try:
            path = request.url.path
            if path.startswith(
                (
                    "/health",
                    "/metrics",
                    "/docs",
                    "/redoc",
                    "/openapi",
                    "/digital-twin",
                )
            ):
                return response

            body = await request.body()
            raw_payload = (
                body.decode("utf-8", errors="ignore") if body else request.url.query
            )
            payload = raw_payload[:500] if raw_payload else None
            ip = request.headers.get("x-forwarded-for") or (
                request.client.host if request.client else None
            )
            geo = request.headers.get("x-geo")
            user = None
            try:
                auth = request.headers.get("authorization", "")
                if auth.startswith("Bearer "):
                    token = auth.split(" ", 1)[1]
                    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                    user = decoded.get("sub")
            except Exception:
                user = None
            latency_ms = (time.time() - start) * 1000

            evt = Event(
                timestamp=datetime.utcnow(),
                tipo="http_request",
                info={
                    "user": user or "anonymous",
                    "endpoint": path,
                    "method": request.method,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                    "ip": ip,
                    "geo": geo,
                    "payload": payload,
                },
                descricao=f"{request.method} {path} status={response.status_code}",
            )
            process_event(evt)
        except Exception:
            logging.exception("Failed to emit security telemetry")
        return response


app.add_middleware(SecurityTelemetryMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ---------- MQTT publisher (delegado para service) ----------
# Usa o serviço isolado `app.services.mqtt_service.mqtt_service` para publicar
def _collect_resources():
    proc = psutil.Process(os.getpid())
    while True:
        CPU_USAGE.set(proc.cpu_percent(interval=None))
        MEM_USAGE.set(proc.memory_info().rss)
        time.sleep(5)


threading.Thread(target=_collect_resources, daemon=True).start()


def publish_balance_update(
    username: str,
    balance: float,
    operation_type: str,
    amount: float,
    to_user: Optional[str] = None,
):
    ev = {
        "timestamp": datetime.utcnow().isoformat(),
        "tipo": operation_type,
        "info": {
            "user": username,
            "amount": amount,
            "balance": balance,
            "to_user": to_user,
        },
        "descricao": f"{username} -> {operation_type} de {amount}, novo saldo={balance}",
    }
    try:
        # publica evento de operação e também atualiza tópico de balance quando aplicável
        mqtt_service.publish_operation(ev)
        mqtt_service.publish_balance(username, balance)
    except Exception:
        # Falha de publicação não deve quebrar fluxo da API
        logging.exception("Falha ao publicar evento no MQTT via mqtt_service")


# ---------- Banco de dados ----------
engine_kwargs: dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs.update(
        {
            "pool_size": int(settings.db_pool_size),
            "max_overflow": int(settings.db_max_overflow),
            "pool_timeout": int(settings.db_pool_timeout),
        }
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# só cria as tabelas automaticamente em SQLite (testes em memória)
if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(engine)
    # migration: add role column if missing (SQLite does not support ALTER TABLE ADD COLUMN idempotently via ORM)
    try:
        with engine.connect() as _conn:
            _conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'user'"
                )
            )
            _conn.commit()
    except Exception:
        pass  # column already exists

# Lock global para operações de escrita
write_lock = threading.Lock()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- utilitários de auth e custo ----------
def estimate_cost(
    cpu_core_price_per_hour, mem_gb_price_per_hour, msg_price_per_million
):
    uptime_seconds = time.time() - START_TIME
    hours = uptime_seconds / 3600
    avg_cpu = CPU_USAGE._value.get() / 100
    cpu_cost = avg_cpu * hours * cpu_core_price_per_hour

    avg_mem_gb = MEM_USAGE._value.get() / 1024**3
    mem_cost = avg_mem_gb * hours * mem_gb_price_per_hour

    total_msgs = MESSAGES_PROCESSED._value.get()
    msg_cost = (total_msgs / 1_000_000) * msg_price_per_million

    return cpu_cost + mem_cost + msg_cost


def get_password_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return get_password_hash(plain) == hashed


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from jwt import InvalidTokenError

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = cast(Optional[str], payload.get("sub"))
        if not username:
            raise creds_exc
    except (InvalidTokenError, JWTError):
        raise creds_exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise creds_exc
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    c = cast(Any, current_user)
    if str(c.role or "user") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


# ---------- Schemas ----------
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class DepositRequest(BaseModel):
    amount: float = Field(
        gt=0, description="O valor do depósito deve ser maior que zero."
    )


class PixRequest(BaseModel):
    to_user: str
    amount: float = Field(gt=0, description="O valor do PIX deve ser maior que zero.")
    payload: Optional[str] = None


class LogOut(BaseModel):
    timestamp: str
    user: str
    action: str


# ---------- Digital Twin + Logger ----------
twin = DigitalTwin()
TELEMETRY_FEED: deque[dict[str, Any]] = deque(maxlen=250)
TELEMETRY_CONDITION = threading.Condition()
telemetry_sequence = 0


def publish_twin_update(event: dict[str, Any]) -> None:
    global telemetry_sequence
    payload = {
        "event": event,
        "stats": twin.stats(),
        "alerts": twin.get_alerts(limit=20),
        "timestamp": datetime.utcnow().isoformat(),
    }
    with TELEMETRY_CONDITION:
        telemetry_sequence += 1
        payload["id"] = telemetry_sequence
        TELEMETRY_FEED.append(payload)
        TELEMETRY_CONDITION.notify_all()


def wait_for_twin_updates(
    last_seen: int, timeout: float = 15.0
) -> tuple[int, list[dict[str, Any]]]:
    with TELEMETRY_CONDITION:
        if telemetry_sequence <= last_seen:
            TELEMETRY_CONDITION.wait(timeout=timeout)
        updates = [item for item in TELEMETRY_FEED if item["id"] > last_seen]
        next_seen = updates[-1]["id"] if updates else last_seen
        return next_seen, updates


def process_event(evt: Event) -> None:
    ev = evt.to_dict()
    start = time.monotonic()
    twin.apply_event(ev)
    anoms = twin.anomalies(ev["info"].get("user"))
    elapsed = time.monotonic() - start

    PROCESS_LATENCY.observe(elapsed)
    MESSAGES_PROCESSED.inc()

    if anoms:
        try:
            mqtt_service.publish_anomaly(anoms[-1])
        except Exception:
            logging.exception("Failed to publish anomaly")

    try:
        mqtt_service.publish_operation(ev)
    except Exception:
        logging.exception("Failed to publish operation event")

    publish_twin_update(ev)


class DigitalTwinHandler(logging.Handler):
    def emit(self, record):
        if record.getMessage() == "anomaly":
            return
        if getattr(record, "skip_twin", False):
            return

        # Build and validate event using Pydantic
        try:
            evt = Event(
                timestamp=datetime.utcnow(),
                tipo=record.getMessage(),
                info={
                    "user": getattr(record, "user", None),
                    "amount": getattr(record, "amount", None),
                    "to_user": getattr(record, "to_user", None),
                    "balance": getattr(record, "balance", None),
                },
                descricao=f"{getattr(record, 'user', '')} fez {record.getMessage()}",
            )
        except Exception:
            logging.exception("Invalid event from log record")
            return

        process_event(evt)


logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(DigitalTwinHandler())


# ---------- Endpoints ----------
@app.get("/cost")
def cost(cpu_price: float, mem_price: float, msg_price: float):
    total = estimate_cost(cpu_price, mem_price, msg_price)
    uptime_seconds = time.time() - START_TIME
    hours = uptime_seconds / 3600
    avg_cpu = CPU_USAGE._value.get() / 100
    avg_mem_gb = MEM_USAGE._value.get() / 1024**3
    total_msgs = MESSAGES_PROCESSED._value.get()
    return {
        "estimated_cost": total,
        "breakdown": {
            "cpu_cost": avg_cpu * hours * cpu_price,
            "memory_cost": avg_mem_gb * hours * mem_price,
            "message_cost": (total_msgs / 1_000_000) * msg_price,
            "uptime_hours": hours,
            "avg_cpu_fraction": avg_cpu,
            "avg_mem_gb": avg_mem_gb,
            "total_messages": total_msgs,
        },
    }


@app.get("/metrics")
def metrics():
    data = generate_latest(registry)
    return Response(data, media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/ping")
def ping():
    return {"pong": True}


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    with write_lock:
        if db.query(User).filter_by(username=user.username).first():
            raise HTTPException(400, "Username already registered")
        _role = (
            user.role
            if user.role
            else ("admin" if user.username == "admin" else "user")
        )
        db_user = User(
            username=user.username,
            hashed_password=get_password_hash(user.password),
            role=_role,
        )
        db.add(db_user)
        db.commit()
        return {"message": "User created"}


@app.post("/digital-twin/logs/upload")
async def upload_logs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    events = process_logs_file(content)
    for raw in events:
        try:
            evt = Event.model_validate(raw)
            process_event(evt)
        except Exception:
            logging.exception("Skipped invalid event during upload")
    return {"imported": len(events)}


@app.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    json_data: Optional[LoginRequest] = None,
    db: Session = Depends(get_db),
):
    # Use either form data or JSON data
    username = (
        form_data.username if form_data else json_data.username if json_data else None
    )
    password = (
        form_data.password if form_data else json_data.password if json_data else None
    )

    print(f"Login attempt - Username: {username}")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials"
        )

    ip = request.client.host if request.client else "unknown"
    if not TESTING and not allow(ip):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas, tente novamente mais tarde.",
        )

    with write_lock:
        user = cast(Any, db.query(User).filter_by(username=username).first())
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token({"sub": user.username})
        db.add(Log(user_id=user.id, action="login", timestamp=datetime.utcnow()))
        db.commit()
        # Ingest event via validated schema
        try:
            evt = Event(
                timestamp=datetime.utcnow(),
                tipo="login",
                info={"user": user.username},
                descricao=f"{user.username} fez login",
            )
            process_event(evt)
        except Exception:
            logging.exception("Failed to process login event")
        logger.info(
            "login", extra={"user": user.username, "action": "login", "skip_twin": True}
        )
        return {"access_token": token, "token_type": "bearer"}


@app.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    current = cast(Any, current_user)
    db.add(Log(user_id=current.id, action="balance", timestamp=datetime.utcnow()))
    db.commit()
    try:
        evt = Event(
            timestamp=datetime.utcnow(),
            tipo="balance",
            info={"user": current.username, "balance": current.balance},
            descricao=f"{current.username} consultou saldo",
        )
        process_event(evt)
    except Exception:
        logging.exception("Failed to process balance event")
    logger.info(
        "balance",
        extra={
            "user": current.username,
            "action": "balance",
            "balance": current.balance,
            "skip_twin": True,
        },
    )
    publish_balance_update(current.username, current.balance, "balance", 0.0)
    return {"balance": current.balance}


@app.post("/deposit")
def deposit(
    req: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")
    current = cast(Any, current_user)

    with write_lock:
        db.execute(
            update(User)
            .where(User.id == current.id)
            .values(balance=User.balance + req.amount)
        )
        db.add(Transaction(user_id=current.id, type="deposit", amount=req.amount))
        db.commit()
        user = cast(Any, db.query(User).filter(User.id == current.id).first())
        publish_balance_update(user.username, user.balance, "deposit", req.amount)
        try:
            evt = Event(
                timestamp=datetime.utcnow(),
                tipo="deposit",
                info={
                    "user": user.username,
                    "amount": req.amount,
                    "balance": user.balance,
                },
                descricao=f"{user.username} depositou {req.amount}",
            )
            process_event(evt)
        except Exception:
            logging.exception("Failed to process deposit event")
        logger.info(
            "deposit",
            extra={
                "user": user.username,
                "amount": req.amount,
                "balance": user.balance,
                "skip_twin": True,
            },
        )
        return {"balance": user.balance}


@app.post("/pix")
def pix(
    req: PixRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    current = cast(Any, current_user)
    with write_lock:
        sender = cast(Any, db.query(User).filter(User.id == current.id).first())
        recipient = cast(
            Any, db.query(User).filter(User.username == req.to_user).first()
        )
        if recipient is None:
            raise HTTPException(status_code=404, detail="Destinatário não encontrado")
        if sender.balance < req.amount:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")
        db.execute(
            update(User)
            .where(User.id == sender.id)
            .values(balance=User.balance - req.amount)
        )
        db.execute(
            update(User)
            .where(User.id == recipient.id)
            .values(balance=User.balance + req.amount)
        )
        db.add_all(
            [
                Transaction(user_id=sender.id, type="pix", amount=req.amount),
                Transaction(
                    user_id=recipient.id, type="pix_received", amount=req.amount
                ),
                Log(user_id=sender.id, action="pix", timestamp=datetime.utcnow()),
                Log(
                    user_id=recipient.id,
                    action="pix_received",
                    timestamp=datetime.utcnow(),
                ),
            ]
        )
        db.commit()
        sender = cast(Any, db.query(User).filter(User.id == sender.id).first())
        recipient = cast(Any, db.query(User).filter(User.id == recipient.id).first())
        publish_balance_update(
            sender.username,
            sender.balance,
            "pix_sent",
            req.amount,
            to_user=recipient.username,
        )
        publish_balance_update(
            recipient.username,
            recipient.balance,
            "pix_received",
            req.amount,
            to_user=sender.username,
        )
        try:
            evt_sender = Event(
                timestamp=datetime.utcnow(),
                tipo="pix_sent",
                info={
                    "user": sender.username,
                    "to_user": recipient.username,
                    "amount": req.amount,
                    "balance": sender.balance,
                    "payload": req.payload,
                },
                descricao=f"{sender.username} enviou PIX para {recipient.username}",
            )
            evt_recipient = Event(
                timestamp=datetime.utcnow(),
                tipo="pix_received",
                info={
                    "user": recipient.username,
                    "to_user": sender.username,
                    "amount": req.amount,
                    "balance": recipient.balance,
                },
                descricao=f"{recipient.username} recebeu PIX de {sender.username}",
            )
            process_event(evt_sender)
            process_event(evt_recipient)
        except Exception:
            logging.exception("Failed to process pix event")
        logger.info(
            "pix",
            extra={
                "user": sender.username,
                "to_user": recipient.username,
                "amount": req.amount,
                "balance": sender.balance,
                "skip_twin": True,
            },
        )
        return {"balance": sender.balance}


@app.get("/logs", response_model=List[LogOut])
def get_logs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    current = cast(Any, current_user)
    logs = cast(list[Any], db.query(Log).filter_by(user_id=current.id).all())
    return [
        LogOut(
            timestamp=log.timestamp.isoformat(),
            user=current.username,
            action=log.action,
        )
        for log in logs
    ]


@app.get("/user/me")
def get_user_me(current_user: User = Depends(get_current_user)):
    current = cast(Any, current_user)
    return {
        "username": current.username,
        "balance": current.balance,
        "role": str(current.role or "user"),
    }


@app.get("/bank/transactions")
def get_bank_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current = cast(Any, current_user)
    txns = cast(
        list[Any],
        db.query(Transaction)
        .filter(Transaction.user_id == current.id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all(),
    )
    return [
        {
            "id": t.id,
            "type": t.type.value if hasattr(t.type, "value") else str(t.type),
            "amount": float(t.amount),
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        }
        for t in txns
    ]


# --- Digital Twin endpoints ---
@app.get("/digital-twin/export/logs")
def export_all_logs(user: Optional[str] = None):
    return twin.export_events(username=user)


@app.get("/digital-twin/summary")
def twin_summary():
    return twin.summary()


@app.get("/digital-twin/stats")
def twin_stats():
    return twin.stats()


@app.get("/digital-twin/sazonalidade")
def twin_sazonalidade():
    return twin.sazonalidade()


@app.get("/digital-twin/shadow/{username}")
def twin_shadow(username: str):
    return twin.get_shadow(username)


@app.get("/digital-twin/code-analysis-logs")
def code_analysis_logs():
    return twin.users["precommit"]["eventos"]


@app.get("/digital-twin/anomalies")
def twin_anomalies(user: Optional[str] = None):
    return twin.anomalies(user)


@app.get("/digital-twin/alerts")
def twin_alerts(limit: int = 50):
    return twin.get_alerts(limit=limit)


@app.get("/digital-twin/stream")
async def twin_stream(request: Request):
    async def event_generator():
        last_seen = telemetry_sequence
        snapshot = {
            "id": last_seen,
            "event": None,
            "stats": twin.stats(),
            "alerts": twin.get_alerts(limit=20),
            "timestamp": datetime.utcnow().isoformat(),
        }
        yield f"event: snapshot\ndata: {json.dumps(snapshot, default=str)}\n\n"

        while not await request.is_disconnected():
            next_seen, updates = await asyncio.to_thread(
                wait_for_twin_updates, last_seen
            )
            if not updates:
                yield ": heartbeat\n\n"
                continue

            for stream_update in updates:
                yield f"id: {stream_update['id']}\nevent: telemetry\ndata: {json.dumps(stream_update, default=str)}\n\n"
            last_seen = next_seen

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/digital-twin/simulate")
def simulate_threats(
    scenario: str,
    user: str = "admin",
    _: User = Depends(require_admin),
):
    now = datetime.utcnow()
    events: List[Event] = []

    if scenario == "fraude_transacional":
        events.append(
            Event(
                timestamp=now,
                tipo="pix_sent",
                info={"user": user, "to_user": "nova_conta", "amount": 500000.0},
                descricao="Simulação: Fraude Transacional (PIX alto)",
            )
        )
    elif scenario == "risco_geografico":
        events.append(
            Event(
                timestamp=now,
                tipo="login",
                info={"user": user, "ip": "203.0.113.88", "geo": "RU"},
                descricao="Simulação: Login de risco geográfico",
            )
        )
        events.append(
            Event(
                timestamp=now,
                tipo="http_request",
                info={
                    "user": user,
                    "endpoint": "/admin/export",
                    "method": "GET",
                    "status": 200,
                    "ip": "203.0.113.88",
                    "geo": "RU",
                },
                descricao="Simulação: Tentativa de extração de dados",
            )
        )
    elif scenario == "appsec_exploit":
        events.append(
            Event(
                timestamp=now,
                tipo="http_request",
                info={
                    "user": user,
                    "endpoint": "/token",
                    "method": "POST",
                    "status": 500,
                    "payload": "' OR 1=1; DROP TABLE users; --",
                },
                descricao="Simulação: AppSec exploit (SQLi)",
            )
        )
    else:
        raise HTTPException(status_code=400, detail="Cenário inválido")

    for evt in events:
        process_event(evt)

    return {"scenario": scenario, "events": len(events), "alerts": twin.get_alerts(10)}


# --- Admin endpoints ---
@app.post("/admin/tests/integration")
def admin_tests_integration(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Executa testes de integração (apenas para admin)"""
    require_admin(current_user)

    results = []

    # Test 1: Health Check
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        results.append(
            {
                "test_name": "API Health",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "duration": 0,
                "message": response.json().get("status"),
            }
        )
    except Exception as e:
        results.append(
            {
                "test_name": "API Health",
                "status": "FAIL",
                "duration": 0,
                "message": str(e),
            }
        )

    # Test 2: Digital Twin Summary
    try:
        response = requests.get("http://localhost:8000/digital-twin/summary", timeout=5)
        results.append(
            {
                "test_name": "Digital Twin Summary",
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "duration": 0,
                "message": "OK"
                if response.status_code == 200
                else f"HTTP {response.status_code}",
            }
        )
    except Exception as e:
        results.append(
            {
                "test_name": "Digital Twin Summary",
                "status": "FAIL",
                "duration": 0,
                "message": str(e),
            }
        )

    # Test 3: Database Connection
    try:
        user_count = db.query(User).count()
        results.append(
            {
                "test_name": "Database Connection",
                "status": "PASS",
                "duration": 0,
                "message": f"{user_count} users in database",
            }
        )
    except Exception as e:
        results.append(
            {
                "test_name": "Database Connection",
                "status": "FAIL",
                "duration": 0,
                "message": str(e),
            }
        )

    return {"results": results}


@app.get("/admin/dashboard/stats")
def admin_dashboard_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Retorna estatísticas do dashboard (apenas para admin)"""
    require_admin(current_user)

    total_users = db.query(User).count()
    total_balance = db.query(User).with_entities(func.sum(User.balance)).scalar() or 0

    return {
        "total_users": total_users,
        "total_balance": total_balance,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Root redirection to frontend (Next.js)
@app.get("/")
def root():
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(frontend_url)


if __name__ == "__main__":
    import uvicorn

    # Usar reload=False para evitar problema com Prometheus CollectorRegistry duplicado
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
