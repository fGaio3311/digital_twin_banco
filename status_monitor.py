#!/usr/bin/env python3
"""
Status Monitor - Monitora o status dos serviços
"""
import requests
import time
from datetime import datetime

def check_frontend():
    """Verifica se o frontend está funcionando"""
    try:
        response = requests.get("http://localhost:3000", timeout=3)
        return response.status_code == 200
    except:
        return False

def check_backend():
    """Verifica se o backend está funcionando"""
    try:
        response = requests.get("http://localhost:8000/ping", timeout=3)
        return response.status_code == 200
    except:
        return False

def test_login():
    """Testa o login completo"""
    try:
        response = requests.post("http://localhost:8000/token",
                               data={"username": "test123", "password": "test123"},
                               timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    """Monitor principal"""
    print("🏦 Sistema Bancário - Monitor de Status")
    print("=" * 50)

    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Status Frontend
        frontend_status = "🟢 ONLINE" if check_frontend() else "🔴 OFFLINE"

        # Status Backend
        backend_status = "🟢 ONLINE" if check_backend() else "🔴 OFFLINE"

        # Status Login
        login_status = "🟢 OK" if test_login() else "🔴 FALHA"

        # Clear screen e show status
        print(f"\r[{timestamp}] Frontend: {frontend_status} | Backend: {backend_status} | Login: {login_status}", end="")

        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Monitor parado")
