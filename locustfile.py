import random
from locust import HttpUser, task, between

def load_tokens():
    with open("tokens.txt") as f:
        return [line.strip() for line in f if line.strip()]

TOKENS = load_tokens()

class BankUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        if not TOKENS:
            raise RuntimeError("Nenhum token carregado; rode o pré-criador.")
        token = random.choice(TOKENS)
        self.headers = {"Authorization": f"Bearer {token}"}

    @task(3)
    def view_balance(self):
        self.client.get("/balance", headers=self.headers, name="/balance")

    @task(2)
    def deposit(self):
        self.client.post("/deposit", headers=self.headers, json={"amount": 10}, name="/deposit")

    @task(1)
    def pix(self):
        self.client.post("/pix", headers=self.headers, json={"to_user": "loadtest-target", "amount": 5}, name="/pix")

    @task(1)
    def get_metrics(self):
        self.client.get("/metrics", name="/metrics")

    @task(1)
    def get_cost(self):
        self.client.get("/cost", params={
            "cpu_price": 0.10,
            "mem_price": 0.05,
            "msg_price": 0.01
        }, name="/cost")
