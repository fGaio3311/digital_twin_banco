# tests/test_twin.py

def test_twin_summary_and_sazonalidade(client):
    # cria eventos
    client.post("/register", json={"username": "twin", "password": "pw"})
    tok = client.post("/token", data={"username": "twin", "password": "pw"}).json()["access_token"]
    client.post("/deposit", json={"amount": 100}, headers={"Authorization": f"Bearer {tok}"})

    # summary
    r = client.get("/digital-twin/summary")
    assert r.status_code == 200
    assert "twin" in r.json()

    # sazonalidade
    r = client.get("/digital-twin/sazonalidade")
    assert r.status_code == 200
    data = r.json()
    assert "by_hour" in data

    # anomalies (if implemented)
    ar = client.get("/digital-twin/anomalies")
    assert ar.status_code == 200
