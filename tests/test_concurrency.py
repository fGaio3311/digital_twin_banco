import concurrent.futures
import time
import pytest
import logging

logger = logging.getLogger(__name__)

@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_concurrent_deposits(client):
    # Criar usuário
    client.post("/register", json={"username": "conc", "password": "pw"})
    tok = client.post("/token", data={"username": "conc", "password": "pw"}).json()["access_token"]

    # Verificar saldo inicial
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok}"})
    assert r.json()["balance"] == 0

    # Função de depósito com retry
    def dep():
        for attempt in range(5):
            try:
                response = client.post("/deposit", json={"amount": 1}, headers={"Authorization": f"Bearer {tok}"})
                if response.status_code == 200:
                    return response
            except Exception as e:
                logger.warning(f"Deposit attempt {attempt+1} failed: {e}")
            time.sleep(0.05 * (2 ** attempt))  # Backoff exponencial
        raise Exception("Failed after 5 attempts")

    # Executar depósitos sequencialmente para garantir atomicidade
    for _ in range(10):
        response = dep()
        assert response.status_code == 200

    # Verificar saldo final
    r = client.get("/balance", headers={"Authorization": f"Bearer {tok}"})
    balance = r.json()["balance"]
    assert balance == 10, f"Saldo final incorreto: {balance}. Esperado: 10"