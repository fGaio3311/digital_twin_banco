# tests/test_api_basic.py
import json

def test_register_and_login(client):
    r = client.post("/register", json={"username": "alice", "password": "pw"})
    assert r.status_code == 200

    r = client.post("/token", data={"username": "alice", "password": "pw"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_balance_deposit_pix_logs(client):
    # setup 2 users
    client.post("/register", json={"username": "alice", "password": "pw"})
    client.post("/register", json={"username": "bob", "password": "pw"})

    tok_a = client.post("/token", data={"username": "alice", "password": "pw"}).json()["access_token"]
    tok_b = client.post("/token", data={"username": "bob", "password": "pw"}).json()["access_token"]

    # balance initial
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok_a}"})
    assert r.status_code == 200
    assert r.json()["balance"] == 0

    # deposit
    r = client.post("/deposit", json={"amount": 100}, headers={"Authorization": f"Bearer {tok_a}"})
    assert r.status_code == 200
    assert r.json()["balance"] == 100

    # pix
    r = client.post("/pix", json={"to_user": "bob", "amount": 40}, headers={"Authorization": f"Bearer {tok_a}"})
    assert r.status_code == 200
    assert r.json()["balance"] == 60

    # bob balance
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok_b}"})
    assert r.json()["balance"] == 40

    # logs
    r = client.get("/logs", headers={"Authorization": f"Bearer {tok_a}"})
    assert r.status_code == 200
    logs = r.json()
    assert any(l["action"] == "balance" for l in logs)
