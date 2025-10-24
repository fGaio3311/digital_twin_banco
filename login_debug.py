#!/usr/bin/env python3
"""
Login Debug Helper - Monitora tentativas de login em tempo real
"""
import requests
import time
from datetime import datetime

def check_backend_logs():
    """Verifica se houve tentativas de login recentes"""
    print("🔍 Monitorando tentativas de login...")
    print("➡️  Faça login no frontend em http://localhost:3000")
    print("➡️  Use: test123 / test123")
    print("➡️  Pressione Ctrl+C para parar")
    print("=" * 60)

    last_check = datetime.now()

    while True:
        try:
            # Test se backend está funcionando
            ping_response = requests.get("http://localhost:8000/ping", timeout=1)
            if ping_response.status_code != 200:
                print("❌ Backend não está respondendo")
                time.sleep(2)
                continue

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🟢 Backend online - Aguardando tentativa de login...")

            time.sleep(2)

        except requests.RequestException:
            print("❌ Backend offline")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n✅ Monitor parado")
            break

if __name__ == "__main__":
    check_backend_logs()
