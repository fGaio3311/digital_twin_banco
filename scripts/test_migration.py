import requests
import sys
from datetime import datetime

def test_endpoints():
    BASE_URL = "http://localhost:8000"

    tests = [
        # Test registration
        {
            "name": "Registro de usuário",
            "method": "POST",
            "url": "/register",
            "data": {"username": "testuser", "password": "testpass"},
            "expected_status": [200, 400]  # 400 se já existir
        },
        # Test login
        {
            "name": "Login",
            "method": "POST",
            "url": "/token",
            "data": {"username": "testuser", "password": "testpass"},
            "expected_status": [200]
        },
        # Test deposit
        {
            "name": "Depósito",
            "method": "POST",
            "url": "/deposit",
            "data": {"amount": 100},
            "needs_auth": True,
            "expected_status": [200]
        },
        # Test balance
        {
            "name": "Consulta saldo",
            "method": "GET",
            "url": "/balance",
            "needs_auth": True,
            "expected_status": [200]
        }
    ]

    token = None

    for test in tests:
        print(f"\n🧪 Testando: {test['name']}")

        headers = {}
        if test.get('needs_auth') and token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if test['method'] == 'GET':
                response = requests.get(f"{BASE_URL}{test['url']}", headers=headers)
            else:
                response = requests.post(f"{BASE_URL}{test['url']}", json=test.get('data'), headers=headers)

            if response.status_code in test['expected_status']:
                print(f"✅ Sucesso! Status: {response.status_code}")
                if test['url'] == '/token' and response.status_code == 200:
                    token = response.json()['access_token']
            else:
                print(f"❌ Erro! Status: {response.status_code}")
                print(f"Resposta: {response.text}")

        except Exception as e:
            print(f"❌ Erro ao testar {test['name']}: {e}")

def main():
    print("🚀 Iniciando testes da API...")
    test_endpoints()

if __name__ == "__main__":
    main()
