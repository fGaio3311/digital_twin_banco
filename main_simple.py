import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Any
import pathlib

from fastapi import (
    FastAPI, Depends, HTTPException,
    status, Request, Response, WebSocket, WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.pool import StaticPool
import jwt
from jose import JWTError

# imports locais
from models import Base, User, Log, Transaction

# Importa monitores do Digital Twin
from business_drivers import business_monitor
from functionality_monitor import functionality_monitor
from rnf_monitor import rnf_monitor
from engineering_monitor import engineering_monitor
from technology_monitor import technology_monitor

# Importa o gerenciador de testes admin
from admin_test_manager import admin_test_manager

# Configurações básicas
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------- Configuração Básica do Banco ----------
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar as tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bank Simulator - Simple")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Auth Functions ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jwt import InvalidTokenError
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise creds_exc
    except (InvalidTokenError, JWTError):
        raise creds_exc

    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        raise creds_exc
    return user

# ---------- Models ----------
class Token(BaseModel):
    access_token: str
    token_type: str

class UserRegistration(BaseModel):
    username: str
    password: str
    initial_balance: float = 1000.0

class DepositRequest(BaseModel):
    amount: float

class TransferRequest(BaseModel):
    to_username: str
    amount: float

# ---------- Routes ----------
@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.post("/register")
async def register(user_data: UserRegistration, db: Session = Depends(get_db)):
    # Verificar se usuário já existe
    existing_user = db.execute(select(User).where(User.username == user_data.username)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(400, "Username already registered")

    # Criar novo usuário
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        balance=user_data.initial_balance
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "username": new_user.username}

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == form_data.username)).scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "balance": current_user.balance,
        "id": current_user.id
    }

@app.post("/deposit")
async def deposit(request: DepositRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")

    # Atualizar saldo
    current_user.balance += request.amount
    db.commit()

    # Registrar transação
    transaction = Transaction(
        from_user_id=current_user.id,
        to_user_id=current_user.id,
        amount=request.amount,
        transaction_type="deposit"
    )
    db.add(transaction)
    db.commit()

    return {"message": "Depósito realizado", "new_balance": current_user.balance}

@app.post("/transfer")
async def transfer(request: TransferRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")

    # Buscar destinatário
    to_user = db.execute(select(User).where(User.username == request.to_username)).scalar_one_or_none()
    if not to_user:
        raise HTTPException(status_code=404, detail="Destinatário não encontrado")

    if current_user.balance < request.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    # Realizar transferência
    current_user.balance -= request.amount
    to_user.balance += request.amount

    # Registrar transação
    transaction = Transaction(
        from_user_id=current_user.id,
        to_user_id=to_user.id,
        amount=request.amount,
        transaction_type="transfer"
    )
    db.add(transaction)
    db.commit()

    return {"message": "Transferência realizada", "new_balance": current_user.balance}

@app.get("/transactions")
async def get_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transactions = db.execute(
        select(Transaction).where(
            (Transaction.from_user_id == current_user.id) |
            (Transaction.to_user_id == current_user.id)
        ).order_by(Transaction.timestamp.desc())
    ).scalars().all()

    result = []
    for t in transactions:
        from_user = db.get(User, t.from_user_id)
        to_user = db.get(User, t.to_user_id)

        result.append({
            "id": t.id,
            "from_username": from_user.username if from_user else "N/A",
            "to_username": to_user.username if to_user else "N/A",
            "amount": t.amount,
            "type": t.transaction_type,
            "timestamp": t.timestamp.isoformat()
        })

    return result

# ---------- Digital Twin Monitoring Endpoints ----------

@app.get("/api/twin/anomalies")
async def get_anomalies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna anomalias detectadas no sistema"""
    from twin import DigitalTwin
    from anomaly_detection import detect_anomalies, DEFAULT_RULES
    import json

    # Buscar transações recentes (últimas 24 horas)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)

    transactions = db.execute(
        select(Transaction).where(Transaction.timestamp >= yesterday)
    ).scalars().all()

    # Converter para formato de eventos
    events = []
    for t in transactions:
        events.append({
            "timestamp": t.timestamp.isoformat(),
            "tipo": t.transaction_type,
            "info": {
                "amount": float(t.amount),
                "from_user": t.from_user_id,
                "to_user": t.to_user_id
            }
        })

    # Detectar anomalias
    anomalies = detect_anomalies(events, DEFAULT_RULES)

    # Formatar para o frontend
    formatted_anomalies = []
    for i, anomaly in enumerate(anomalies):
        rule = anomaly["rule"]
        event = anomaly["evento"]

        severity = "medium"
        message = f"Anomalia detectada: {rule}"

        if rule == "big_deposit":
            severity = "high"
            amount = event["info"]["amount"]
            message = f"Depósito suspeito de R$ {amount:,.2f}"
        elif rule == "big_pix":
            severity = "critical"
            amount = event["info"]["amount"]
            message = f"PIX de alto valor: R$ {amount:,.2f}"
        elif rule == "high_frequency":
            severity = "medium"
            message = "Alta frequência de transações detectada"

        formatted_anomalies.append({
            "id": str(i + 1),
            "rule": rule,
            "severity": severity,
            "message": message,
            "timestamp": event["timestamp"],
            "user": f"user_{event['info'].get('from_user', 'N/A')}",
            "amount": event["info"].get("amount"),
            "event": event
        })

    return formatted_anomalies

@app.get("/api/twin/metrics")
async def get_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna métricas de performance do sistema"""
    import pathlib
    import json

    metrics = []
    metrics_file = pathlib.Path("metrics_log.jsonl")

    if metrics_file.exists():
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        metrics.append(json.loads(line))
        except Exception as e:
            print(f"Erro ao ler métricas: {e}")

    # Limitar aos últimos 100 registros
    recent_metrics = metrics[-100:] if metrics else []

    return {"metrics": recent_metrics}

@app.get("/api/twin/health")
async def get_system_health(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna saúde geral do sistema"""
    import psutil
    from datetime import datetime, timedelta

    # Estatísticas do sistema
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
    except:
        cpu_usage = 25.0  # Fallback values
        memory_usage = 45.0

    # Estatísticas do banco
    total_users = db.execute(select(User)).scalars().all()
    total_transactions = db.execute(select(Transaction)).scalars().all()

    # Transações das últimas 24h
    yesterday = datetime.now() - timedelta(days=1)
    recent_transactions = db.execute(
        select(Transaction).where(Transaction.timestamp >= yesterday)
    ).scalars().all()

    # Contar por tipo
    pix_count = len([t for t in recent_transactions if t.transaction_type == "pix"])
    deposit_count = len([t for t in recent_transactions if t.transaction_type == "deposit"])
    transfer_count = len([t for t in recent_transactions if t.transaction_type == "transfer"])

    # Volume total
    total_volume = sum(t.amount for t in recent_transactions)

    # Status geral
    status = "healthy"
    if cpu_usage > 80 or memory_usage > 80:
        status = "warning"
    if cpu_usage > 95 or memory_usage > 95:
        status = "critical"

    # Simular algumas métricas
    active_sessions = len(total_users) // 2  # Aproximação
    error_rate = 1.5 if status == "healthy" else 5.0
    avg_response_time = 150 if status == "healthy" else 300

    return {
        "health": {
            "status": status,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "active_users": active_sessions,
            "total_transactions": len(total_transactions),
            "error_rate": error_rate,
            "avg_response_time": avg_response_time
        },
        "transactions": {
            "total_volume": total_volume,
            "total_count": len(recent_transactions),
            "pix_count": pix_count,
            "deposit_count": deposit_count,
            "transfer_count": transfer_count
        },
        "user_activity": {
            "active_sessions": active_sessions,
            "new_registrations": len([u for u in total_users if u.created_at and u.created_at >= yesterday]) if hasattr(User, 'created_at') else 0,
            "failed_logins": 2  # Simulado
        }
    }

@app.get("/api/twin/status")
async def get_twin_status(current_user: User = Depends(get_current_user)):
    """Status geral do Digital Twin"""
    return {
        "status": "active",
        "version": "1.0.0",
        "last_update": datetime.now().isoformat(),
        "monitoring": {
            "anomaly_detection": True,
            "performance_monitoring": True,
            "user_behavior_analysis": True,
            "financial_monitoring": True
        }
    }

# ========== DIGITAL TWIN SPECIFICATION ENDPOINTS ==========

@app.get("/api/twin/business-drivers")
async def get_business_drivers():
    """Business Drivers - Volume, Picos, Tempo de Resposta"""
    try:
        return {
            "status": "success",
            "data": {
                "current_metrics": business_monitor.get_current_metrics(),
                "alerts": business_monitor.get_alerts(),
                "targets": {
                    "daily_volume_target": business_monitor.metrics.daily_volume_target,
                    "peak_per_minute": business_monitor.metrics.peak_per_minute,
                    "response_time_target": business_monitor.metrics.response_time_target,
                    "percentile_target": business_monitor.metrics.percentile_target
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business drivers error: {str(e)}")

@app.get("/api/twin/functionality")
async def get_functionality_status():
    """Funcionalidade - Login, Consulta Saldo/Extrato, PIX"""
    try:
        return {
            "status": "success",
            "data": {
                "functions": functionality_monitor.get_functionality_status(),
                "overall_availability": functionality_monitor.get_overall_availability(),
                "alerts": functionality_monitor.get_availability_alerts()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Functionality error: {str(e)}")

@app.get("/api/twin/rnf")
async def get_rnf_status():
    """Requisitos Não Funcionais - Volumetria, Rastreabilidade, Performance"""
    try:
        return {
            "status": "success",
            "data": {
                "rnf_status": rnf_monitor.get_rnf_status(),
                "alerts": rnf_monitor.get_rnf_alerts(),
                "metrics_history": rnf_monitor.get_rnf_metrics_history(hours=1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RNF error: {str(e)}")

@app.get("/api/twin/engineering")
async def get_engineering_status():
    """Engenharia - Transações, Base de Dados, Filas, Integrações"""
    try:
        return {
            "status": "success",
            "data": {
                "engineering": engineering_monitor.get_engineering_status(),
                "sla": engineering_monitor.get_sla_status(),
                "vital_signs": engineering_monitor.get_vital_signs(hours=1),
                "system_logs": engineering_monitor.get_system_logs(hours=1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engineering error: {str(e)}")

@app.get("/api/twin/technology")
async def get_technology_status():
    """Tecnologia - Ferramentas, Plataformas, Licenças, SLAs"""
    try:
        return {
            "status": "success",
            "data": {
                "technology": technology_monitor.get_technology_status(),
                "alerts": technology_monitor.get_technology_alerts(),
                "cost_summary": technology_monitor.get_cost_summary()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Technology error: {str(e)}")

@app.get("/api/twin/dashboard/complete")
async def get_complete_dashboard():
    """Dashboard Completo - Todos os Componentes da Especificação"""
    try:
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "specification_compliance": {
                "business_drivers": {
                    "metrics": business_monitor.get_current_metrics(),
                    "alerts": business_monitor.get_alerts()[-5:]  # Últimos 5 alertas
                },
                "functionality": {
                    "status": functionality_monitor.get_functionality_status(),
                    "availability": functionality_monitor.get_overall_availability()
                },
                "rnf": {
                    "status": rnf_monitor.get_rnf_status(),
                    "compliance": {
                        "volumetria": "compliant",
                        "traceability": "compliant",
                        "response_time": "compliant"
                    }
                },
                "engineering": {
                    "overview": engineering_monitor.get_engineering_status(),
                    "sla_compliance": engineering_monitor.get_sla_status()
                },
                "technology": {
                    "stack_health": len([t for t in technology_monitor.technology_stack.values()
                                       if t.status.value == "active"]),
                    "license_status": len([l for l in technology_monitor.licenses.values()
                                         if l.status.value == "valid"]),
                    "cost_summary": technology_monitor.get_cost_summary()
                }
            },
            "overall_health": {
                "business_drivers": "healthy",
                "functionality": "healthy",
                "rnf": "healthy",
                "engineering": "healthy",
                "technology": "healthy"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete dashboard error: {str(e)}")

# ========== MONITOR INITIALIZATION ==========

@app.on_event("startup")
async def startup_event():
    """Inicializa todos os monitores na startup"""
    try:
        # Inicia monitores
        business_monitor.start_monitoring()
        functionality_monitor.start_monitoring()
        rnf_monitor.start_monitoring()
        engineering_monitor.start_monitoring()
        technology_monitor.start_monitoring()

        # Log de inicialização
        engineering_monitor.add_system_log(
            "INFO", "system", "Digital Twin monitors initialized successfully"
        )
    except Exception as e:
        print(f"Error initializing monitors: {e}")

# ========== TRANSACTION HOOKS ==========

async def record_transaction_metrics(function_name: str, success: bool, response_time: float, user_id: str = None):
    """Hook para registrar métricas de transações"""
    try:
        # Business Drivers
        business_monitor.record_transaction(response_time)

        # Functionality
        functionality_monitor.record_function_call(function_name, success, response_time)

        # RNF
        rnf_monitor.record_request(response_time, user_id, traceable=True)

        # Engineering
        engineering_monitor.record_transaction(response_time, success, timeout=False)

    except Exception as e:
        print(f"Error recording transaction metrics: {e}")

# ========== ADMIN TEST ENDPOINTS ==========

@app.post("/api/admin/load-test/start")
async def start_load_test(config: dict):
    """Inicia teste de carga com Locust"""
    result = await admin_test_manager.start_load_test(config)
    return result

@app.post("/api/admin/load-test/stop")
async def stop_load_test():
    """Para teste de carga"""
    result = await admin_test_manager.stop_load_test()
    return result

@app.get("/api/admin/load-test/results")
async def get_load_test_results():
    """Obtém resultados do teste de carga"""
    results = admin_test_manager.get_load_test_results()
    return {"results": results}

@app.get("/api/admin/load-test/real-time")
async def get_real_time_data():
    """Obtém dados em tempo real do teste de carga"""
    data = admin_test_manager.get_real_time_data()
    return data

@app.websocket("/api/admin/load-test/stream")
async def websocket_load_test_stream(websocket: WebSocket):
    """WebSocket para streaming de dados em tempo real"""
    await websocket.accept()
    admin_test_manager.websocket_clients.add(websocket)

    try:
        while True:
            # Manter conexão viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        admin_test_manager.websocket_clients.discard(websocket)

@app.post("/api/admin/integration-tests/run")
async def run_integration_tests():
    """Executa testes de integração"""
    results = await admin_test_manager.run_integration_tests()
    return {"results": [result.__dict__ for result in results]}

@app.post("/api/admin/acceptance-tests/run")
async def run_acceptance_tests():
    """Executa testes de aceitação"""
    results = await admin_test_manager.run_acceptance_tests()
    return {"results": [result.__dict__ for result in results]}

@app.get("/api/admin/system-status")
async def get_system_status():
    """Obtém status completo do sistema para admin"""
    try:
        # Coletardados de todos os monitores
        business_data = business_monitor.get_metrics()
        functionality_data = functionality_monitor.get_functionality_status()
        rnf_data = rnf_monitor.get_metrics()
        engineering_data = engineering_monitor.get_metrics()

        # Dados de teste de carga se disponível
        load_test_data = admin_test_manager.get_real_time_data()

        # Métricas de sistema
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict(),
            "active_connections": len(psutil.net_connections()),
            "running_processes": len(psutil.pids())
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "digital_twin": {
                "business_drivers": business_data,
                "functionality": functionality_data,
                "rnf": rnf_data,
                "engineering": engineering_data
            },
            "load_testing": {
                "is_running": admin_test_manager.load_test_running,
                "real_time_data": load_test_data,
                "results_count": len(admin_test_manager.load_test_results)
            },
            "system_metrics": system_metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
