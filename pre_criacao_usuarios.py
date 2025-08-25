import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "http://localhost:8000"
USERS = 100  # ajuste para quantos tokens quer pré-criar
TARGET_USER = "loadtest-target"
PASSWORD = "pass"
MAX_WORKERS = 20
RETRIES = 3
BACKOFF_BASE = 0.5  # segundos

def safe_post(path, **kwargs):
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.post(f"{API}{path}", timeout=5, **kwargs)
            return resp
        except requests.RequestException as e:
            if attempt == RETRIES:
                return None
            time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
    return None  # unreachable

def ensure_target_user():
    # cria o usuário destino uma vez (ignora se já existe)
    safe_post("/register", json={"username": TARGET_USER, "password": PASSWORD})

def make_user(i):
    username = f"loadtest{i}"
    # registra (pode já existir)
    safe_post("/register", json={"username": username, "password": PASSWORD})

    # login para pegar token
    resp = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.post(f"{API}/token", data={"username": username, "password": PASSWORD}, timeout=5)
            if resp is not None and resp.status_code == 200:
                token = resp.json().get("access_token")
                return token
            else:
                # falhou, espera backoff e tenta de novo
                time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
        except requests.RequestException:
            if attempt == RETRIES:
                return None
            time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
    return None

def main():
    ensure_target_user()

    tokens = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(make_user, i): i for i in range(USERS)}
        for fut in as_completed(futures):
            token = fut.result()
            if token:
                tokens.append(token)

    unique = sorted(set(tokens))
    print(f"[+] Gerados {len(unique)} tokens válidos de {USERS} tentativas.")
    if not unique:
        print("[-] Nenhum token válido, verifique se a API está acessível em", API)
        return

    with open("tokens.txt", "w") as f:
        for t in unique:
            f.write(t + "\n")
    print("[+] Salvo em tokens.txt")

if __name__ == "__main__":
    main()
