# tests/conftest.py
import os

# IMPORTANTE: definir TESTING antes de importar o main
os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.main as main  # certifica-se de que main já veja TESTING="1"
from app.main import app, get_db
from app.models.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False, "timeout": 30.0},
        poolclass=StaticPool,
    )
    # cria todas as tabelas aqui
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def client(engine, monkeypatch):
    # monta um sessionmaker de teste que usa o engine acima
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # override de dependência
    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db

    # desliga MQTT nos testes
    monkeypatch.setattr("main.publish_balance_update", lambda *args, **kwargs: None)

    return TestClient(app)


def auth_token(client):
    client.post("/register", json={"username": "u", "password": "p"})
    resp = client.post("/token", data={"username": "u", "password": "p"})
    return resp.json()["access_token"]
