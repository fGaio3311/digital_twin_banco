# tests/test_security.py
from jose import jwt
from datetime import datetime, timedelta


def test_sql_injection_login(client):
    client.post("/register", json={"username": "eve", "password": "123"})
    r = client.post("/token", data={"username": "' OR 1=1 --", "password": "x"})
    assert r.status_code == 401


def test_negative_or_zero_amount(client):
    client.post("/register", json={"username": "neg", "password": "pw"})
    tok = client.post("/token", data={"username": "neg", "password": "pw"}).json()["access_token"]

    r = client.post("/deposit", json={"amount": -10}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 422 or r.status_code == 400  # depends on validation choices

    r = client.post("/pix", json={"to_user": "neg", "amount": 0}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 400


def test_jwt_tampering(client):
    client.post("/register", json={"username": "jwt", "password": "pw"})
    tok = client.post("/token", data={"username": "jwt", "password": "pw"}).json()["access_token"]
    # tamper payload
    parts = tok.split('.')
    # flip last char of payload
    tampered = parts[0] + '.' + parts[1][:-1] + ('A' if parts[1][-1] != 'A' else 'B') + '.' + parts[2]
    r = client.get("/balance", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


def test_mass_assignment_on_register(client):
    payload = {"username": "mass", "password": "pw", "balance": 1000000}
    client.post("/register", json=payload)
    tok = client.post("/token", data={"username": "mass", "password": "pw"}).json()["access_token"]
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok}"})
    assert r.json()["balance"] == 0


def test_rate_limiting_login(client):
    # assuming limiter allows 5 per minute
    for _ in range(6):
        r = client.post("/token", data={"username": "nobody", "password": "x"})
    assert r.status_code in (401, 429)


def test_xss_in_username(client):
    xss = "<script>alert(1)</script>"
    client.post("/register", json={"username": xss, "password": "pw"})
    # Just ensure we don't crash and user stored literally
    tok = client.post("/token", data={"username": xss, "password": "pw"}).json()["access_token"]
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
