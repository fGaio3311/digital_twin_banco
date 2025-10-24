#!/usr/bin/env python3
"""
Status completo do sistema bancário
"""
import requests
import time
from datetime import datetime

def check_status():
    """Verifica status de todos os serviços"""
    print("🏦 SISTEMA BANCÁRIO DIGITAL TWIN")
    print("=" * 50)

    # Backend status
    try:
        ping_response = requests.get("http://localhost:8000/ping", timeout=3)
        if ping_response.status_code == 200:
            print("✅ Backend: ONLINE")
            print("   📍 URL: http://localhost:8000")
            print("   📖 Docs: http://localhost:8000/docs")

            # Test login
            login_response = requests.post("http://localhost:8000/token",
                                         data={"username": "test123", "password": "test123"},
                                         timeout=3)
            if login_response.status_code == 200:
                print("   🔐 Login: FUNCIONANDO")
                print("   👤 User: test123/test123")
            else:
                print("   ❌ Login: ERRO")
        else:
            print("❌ Backend: OFFLINE")
    except Exception as e:
        print("❌ Backend: OFFLINE")
        print(f"   Error: {e}")

    print()

    # Frontend status
    try:
        frontend_response = requests.get("http://localhost:3000", timeout=3)
        if frontend_response.status_code == 200:
            print("✅ Frontend: ONLINE")
            print("   📍 URL: http://localhost:3000")
            print("   🎨 Interface: React + Material-UI")
        else:
            print("❌ Frontend: OFFLINE")
    except Exception as e:
        print("❌ Frontend: OFFLINE")
        print(f"   Error: {e}")

    print()
    print("🚀 INSTRUÇÕES DE USO:")
    print("1. Acesse: http://localhost:3000")
    print("2. Login: test123")
    print("3. Senha: test123")
    print("4. Explore: Dashboard, Transferências, Transações")
    print()
    print("🔧 Para parar os serviços:")
    print("   - Feche os terminais ou pressione Ctrl+C")

if __name__ == "__main__":
    check_status()
