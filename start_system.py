#!/usr/bin/env python3
"""
Script para inicializar o projeto completo
"""
import sys
import subprocess
import time
import requests
import json
import os
from pathlib import Path

def start_backend():
    """Inicia o servidor backend"""
    print("🚀 Iniciando servidor backend...")

    # Usar o diretório do script como working directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Iniciar servidor em background
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main_simple:app",
        "--host", "0.0.0.0", "--port", "8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Esperar servidor inicializar
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/ping", timeout=2)
            if response.status_code == 200:
                print("✅ Backend iniciado com sucesso!")
                return process
        except:
            pass
        time.sleep(1)

    print("❌ Erro ao iniciar backend")
    return None

def create_test_user():
    """Cria usuário de teste"""
    print("👤 Criando usuário de teste...")

    try:
        # Tentar criar usuário
        response = requests.post("http://localhost:8000/register",
                               json={"username": "test123", "password": "test123", "initial_balance": 1000.0},
                               timeout=5)

        if response.status_code == 200:
            print("✅ Usuário de teste criado!")
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️  Usuário de teste já existe")
        else:
            print(f"⚠️  Erro ao criar usuário: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")

def test_login():
    """Testa o login"""
    print("🔐 Testando login...")

    try:
        response = requests.post("http://localhost:8000/token",
                               data={"username": "test123", "password": "test123"},
                               timeout=5)

        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login funcionando! Token: {token_data['access_token'][:20]}...")
            return token_data['access_token']
        else:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Erro no teste de login: {e}")
        return None

def test_user_info(token):
    """Testa informações do usuário"""
    print("📊 Testando informações do usuário...")

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:8000/user/me", headers=headers, timeout=5)

        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Usuário: {user_data['username']}, Saldo: R$ {user_data['balance']}")
        else:
            print(f"❌ Erro ao obter dados do usuário: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro no teste de dados: {e}")

def main():
    """Função principal"""
    print("🏦 Iniciando Sistema Bancário Digital Twin")
    print("=" * 50)

    # Iniciar backend
    backend_process = start_backend()
    if not backend_process:
        return

    try:
        # Aguardar estabilização
        time.sleep(2)

        # Criar usuário de teste
        create_test_user()

        # Testar login
        token = test_login()

        if token:
            # Testar dados do usuário
            test_user_info(token)

        print("\n" + "=" * 50)
        print("🎉 Sistema iniciado com sucesso!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📖 Docs: http://localhost:8000/docs")
        print("\n👤 Credenciais de teste:")
        print("   Usuário: test123")
        print("   Senha: test123")
        print("\nPressione Ctrl+C para parar o servidor...")

        # Manter servidor rodando
        backend_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Parando servidor...")
        backend_process.terminate()
        backend_process.wait()
        print("✅ Servidor parado")

if __name__ == "__main__":
    main()
