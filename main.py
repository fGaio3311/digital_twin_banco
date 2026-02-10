import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Any
import time
import threading
import psutil
import pathlib
from urllib.parse import urlparse
import requests

import psycopg2  # necessário para wait_for_postgres
from fastapi import (
    FastAPI, Depends, HTTPException,
    status, Request, Response, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, update, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import StaticPool
import jwt
from jose import JWTError
from paho.mqtt import client as mqtt_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

# imports locais
from models import Base, User, Log, Transaction
from app.settings import Settings
from twin import DigitalTwin
from middleware.limiter import allow
from app.utils import process_logs_file

# ---------- Métricas Prometheus ----------
# Usar um registry separado para evitar duplicação
from prometheus_client import CollectorRegistry
registry = CollectorRegistry()

PROCESS_LATENCY = Histogram(
    'dt_process_latency_seconds',
    'Tempo para aplicar um evento no Digital Twin',
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1, 2],
    registry=registry
)
MESSAGES_PROCESSED = Counter(
    'dt_messages_processed_total',
    'Total de eventos processados pelo Digital Twin',
    registry=registry
)
CPU_USAGE = Gauge('dt_cpu_percent', 'Percentual de CPU usado pelo DT', registry=registry)
MEM_USAGE = Gauge('dt_mem_bytes', 'Uso de memória RAM (RSS) pelo DT', registry=registry)

# registra o início para cálculo de uptime
START_TIME = time.time()

# arquivo de log de métricas (JSON Lines)
METRICS_LOG_PATH = pathlib.Path("metrics_log.jsonl")

TESTING = os.getenv("TESTING", "0") == "1"

settings = Settings()
settings.require_api_fields()

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

if settings.database_url.startswith("postgres"):
    wait_for_postgres(settings.database_url)

# ---------- FastAPI ----------
app = FastAPI(
    title=settings.title,
    description="Bank Simulator with Digital Twin",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ---------- Autenticação (precisa antes do middleware que decodifica token) ----------
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# ---------- registro de eventos customizados (para plotting etc) ----------
def record_event(endpoint: str, latency: float, success: bool, user: Optional[str] = None, extra: dict = None):
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
        logging.warning(f"Failed to write metrics log: {e}")  # não quebra a API por falha de log

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------- MQTT publisher ----------
try:
    mqtt_client_global = mqtt_client.Client(
        client_id="api-publisher",
        protocol=mqtt_client.MQTTv311,
    )
    mqtt_client_global.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
    mqtt_client_global.loop_start()
except Exception as e:
    print(f"[MQTT ERRO] Falha ao conectar: {e}")
    mqtt_client_global = None

def _collect_resources():
    proc = psutil.Process(os.getpid())
    while True:
        CPU_USAGE.set(proc.cpu_percent(interval=None))
        MEM_USAGE.set(proc.memory_info().rss)
        time.sleep(5)

threading.Thread(target=_collect_resources, daemon=True).start()

def publish_balance_update(username: str, balance: float, operation_type: str, amount: float):
    if not mqtt_client_global:
        return
    ev = {
        "timestamp": datetime.utcnow().isoformat(),
        "tipo": operation_type,
        "info": {"user": username, "amount": amount, "balance": balance},
        "descricao": f"{username} -> {operation_type} de {amount}, novo saldo={balance}",
    }
    mqtt_client_global.publish(f"banco/{username}/events", json.dumps(ev), qos=1)

# ---------- Banco de dados ----------
engine_kwargs: dict[str, Any] = {}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs.update({
        "pool_size": int(settings.db_pool_size),
        "max_overflow": int(settings.db_max_overflow),
        "pool_timeout": int(settings.db_pool_timeout),
    })

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# só cria as tabelas automaticamente em SQLite (testes em memória)
if settings.database_url.startswith("sqlite"):
    Base.metadata.create_all(engine)

# Lock global para operações de escrita
write_lock = threading.Lock()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- utilitários de auth e custo ----------
def estimate_cost(cpu_core_price_per_hour, mem_gb_price_per_hour, msg_price_per_million):
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

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from jwt import InvalidTokenError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise creds_exc
    except (InvalidTokenError, JWTError):
        raise creds_exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise creds_exc
    return user

# ---------- Schemas ----------
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class DepositRequest(BaseModel):
    amount: float = Field(gt=0, description="O valor do depósito deve ser maior que zero.")

class PixRequest(BaseModel):
    to_user: str
    amount: float = Field(gt=0, description="O valor do PIX deve ser maior que zero.")

class LogOut(BaseModel):
    timestamp: str
    user: str
    action: str

# ---------- Digital Twin + Logger ----------
twin = DigitalTwin()

class DigitalTwinHandler(logging.Handler):
    def emit(self, record):
        if record.getMessage() == "anomaly":
            return

        ev = {
            "timestamp": datetime.utcnow().isoformat(),
            "tipo": record.getMessage(),
            "info": {
                "user": getattr(record, "user", None),
                "amount": getattr(record, "amount", None),
                "to_user": getattr(record, "to_user", None),
            },
            "descricao": f"{getattr(record, 'user', '')} fez {record.getMessage()}"
        }

        start = time.monotonic()
        twin.apply_event(ev)
        anoms = twin.anomalies(ev["info"].get("user"))
        elapsed = time.monotonic() - start

        PROCESS_LATENCY.observe(elapsed)
        MESSAGES_PROCESSED.inc()

        if anoms and mqtt_client_global:
            mqtt_client_global.publish("banco/anomalies", json.dumps(anoms[-1]), qos=0)

        if mqtt_client_global:
            mqtt_client_global.publish(
                f"banco/{ev['info'].get('user','anon')}/events",
                json.dumps(ev),
                qos=1
            )

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(DigitalTwinHandler())

# ---------- Endpoints ----------
@app.get("/cost")
def cost(
    cpu_price: float,
    mem_price: float,
    msg_price: float
):
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
            "total_messages": total_msgs
        }
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
        db_user = User(username=user.username, hashed_password=get_password_hash(user.password))
        db.add(db_user)
        db.commit()
        return {"message": "User created"}

@app.post("/digital-twin/logs/upload")
async def upload_logs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    events = process_logs_file(content)
    for ev in events:
        twin.apply_event(ev)
    return {"imported": len(events)}

@app.post("/token", response_model=Token)
async def login(
    request: Request = None,
    form_data: OAuth2PasswordRequestForm = Depends(),
    json_data: LoginRequest = None,
    db: Session = Depends(get_db)
):
    # Use either form data or JSON data
    username = form_data.username if form_data else json_data.username if json_data else None
    password = form_data.password if form_data else json_data.password if json_data else None

    print(f"Login attempt - Username: {username}")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing credentials"
        )

    ip = request.client.host if request else "unknown"
    if not TESTING and not allow(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Muitas tentativas, tente novamente mais tarde.")


    with write_lock:
        user = db.query(User).filter_by(username=username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Credenciais inválidas",
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = create_access_token({"sub": user.username})
        db.add(Log(user_id=user.id, action="login", timestamp=datetime.utcnow()))
        db.commit()
        logger.info("login", extra={"user": user.username, "action": "login"})
        return {"access_token": token, "token_type": "bearer"}

@app.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.add(Log(user_id=current_user.id, action="balance", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("balance", extra={"user": current_user.username, "action": "balance"})
    return {"balance": current_user.balance}

@app.post("/deposit")
def deposit(
    req: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")

    with write_lock:
        db.execute(
            update(User)
            .where(User.id == current_user.id)
            .values(balance=User.balance + req.amount)
        )
        db.add(Transaction(
            user_id=current_user.id,
            type="deposit",
            amount=req.amount
        ))
        db.commit()
        user = db.query(User).filter(User.id == current_user.id).first()
        publish_balance_update(
            user.username,
            user.balance,
            "deposit",
            req.amount
        )
        logger.info(
            "deposit",
            extra={"user": user.username, "amount": req.amount}
        )
        return {"balance": user.balance}

@app.post("/pix")
def pix(
    req: PixRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    with write_lock:
        sender = db.query(User).filter(User.id == current_user.id).first()
        recipient = db.query(User).filter(User.username == req.to_user).first()
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
        db.add_all([
            Transaction(user_id=sender.id, type="pix", amount=req.amount),
            Transaction(user_id=recipient.id, type="pix_received", amount=req.amount),
            Log(user_id=sender.id, action="pix", timestamp=datetime.utcnow()),
            Log(user_id=recipient.id, action="pix_received", timestamp=datetime.utcnow())
        ])
        db.commit()
        sender = db.query(User).filter(User.id == sender.id).first()
        recipient = db.query(User).filter(User.id == recipient.id).first()
        publish_balance_update(sender.username, sender.balance, "pix_sent", req.amount)
        publish_balance_update(recipient.username, recipient.balance, "pix_received", req.amount)
        logger.info(
            "pix",
            extra={
                "user": sender.username,
                "to_user": recipient.username,
                "amount": req.amount
            }
        )
        return {"balance": sender.balance}

@app.get("/logs", response_model=List[LogOut])
def get_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(Log).filter_by(user_id=current_user.id).all()
    return [
        LogOut(timestamp=log.timestamp.isoformat(),
               user=current_user.username,
               action=log.action)
        for log in logs
    ]

@app.get("/user/me")
def get_user_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "balance": current_user.balance
    }

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

# --- Admin endpoints ---
@app.post("/admin/tests/integration")
async def admin_tests_integration(current_user: User = Depends(get_current_user)):
    """Executa testes de integração (apenas para admin)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")

    results = []

    # Test 1: Health Check
    try:
        response = requests.get(f"http://localhost:8000/health", timeout=5)
        results.append({
            "test_name": "API Health",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "duration": 0,
            "message": response.json().get("status")
        })
    except Exception as e:
        results.append({
            "test_name": "API Health",
            "status": "FAIL",
            "duration": 0,
            "message": str(e)
        })

    # Test 2: Digital Twin Summary
    try:
        response = requests.get(f"http://localhost:8000/digital-twin/summary", timeout=5)
        results.append({
            "test_name": "Digital Twin Summary",
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "duration": 0,
            "message": "OK" if response.status_code == 200 else f"HTTP {response.status_code}"
        })
    except Exception as e:
        results.append({
            "test_name": "Digital Twin Summary",
            "status": "FAIL",
            "duration": 0,
            "message": str(e)
        })

    # Test 3: Database Connection
    try:
        user_count = db.query(User).count()
        results.append({
            "test_name": "Database Connection",
            "status": "PASS",
            "duration": 0,
            "message": f"{user_count} users in database"
        })
    except Exception as e:
        results.append({
            "test_name": "Database Connection",
            "status": "FAIL",
            "duration": 0,
            "message": str(e)
        })

    return {"results": results}

@app.get("/admin/dashboard/stats")
def admin_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna estatísticas do dashboard (apenas para admin)"""
    if current_user.username != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")

    total_users = db.query(User).count()
    total_balance = db.query(User).with_entities(func.sum(User.balance)).scalar() or 0

    return {
        "total_users": total_users,
        "total_balance": total_balance,
        "timestamp": datetime.utcnow().isoformat()
    }

# Servir frontend estático
from pathlib import Path
frontend_path = Path(__file__).parent / "frontend" / "build"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Usar reload=False para evitar problema com Prometheus CollectorRegistry duplicado
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
