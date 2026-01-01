#!/usr/bin/env python3
"""Script para criar usuários de teste no banco de dados"""

import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib

# Criar engine
database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})

# Criar tabelas
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_password_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def create_test_users():
    """Cria usuários de teste"""
    db = SessionLocal()

    test_users = [
        {"username": "admin", "password": "admin123", "balance": 10000.0},
        {"username": "user1", "password": "user123", "balance": 5000.0},
        {"username": "user2", "password": "user123", "balance": 3000.0},
        {"username": "test", "password": "test123", "balance": 1000.0},
    ]

    for user_data in test_users:
        existing = db.query(User).filter_by(username=user_data["username"]).first()

        if not existing:
            new_user = User(
                username=user_data["username"],
                hashed_password=get_password_hash(user_data["password"]),
                balance=user_data["balance"]
            )
            db.add(new_user)
            print(f"✓ Usuário '{user_data['username']}' criado (senha: {user_data['password']})")
        else:
            print(f"✓ Usuário '{user_data['username']}' já existe")

    db.commit()
    db.close()

    print("\n" + "="*50)
    print("CREDENCIAIS DE TESTE")
    print("="*50)
    print("🔑 Administrador:")
    print("   Email: admin")
    print("   Senha: admin123")
    print("\n👤 Usuários de Teste:")
    print("   Email: user1 / user2 / test")
    print("   Senha: user123 / user123 / test123")
    print("\n🌐 Acesse: http://localhost:3000")
    print("="*50 + "\n")

if __name__ == "__main__":
    try:
        create_test_users()
        print("✅ Usuários de teste criados com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar usuários: {e}")
        sys.exit(1)
