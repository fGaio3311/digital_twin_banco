import requests

BASE = "http://localhost:8000"

# registra e obtém token
r = requests.post(f"{BASE}/register", json={"username": "tester", "password": "pass"}, timeout=10)
r = requests.post(f"{BASE}/token", data={"username": "tester", "password": "pass"}, timeout=10)
tok = r.json()["access_token"]
headers = {"Authorization": f"Bearer {tok}"}

# faz várias chamadas
for _ in range(5):
    requests.get(f"{BASE}/balance", headers=headers, timeout=10)
    requests.post(f"{BASE}/deposit", headers=headers, json={"amount": 10}, timeout=10)
