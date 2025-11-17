# cli.py
import json
from pathlib import Path

import requests
import typer

APP = typer.Typer(help="CLI do Banco + Digital Twin")
API_URL_DEFAULT = "http://localhost:8000"
TOKEN_FILE = Path(".token")

def _bar_chart(mapping: dict[int, int] | dict[str, int], width: int = 40):
    max_v = max(mapping.values()) if mapping else 1
    for k, v in mapping.items():
        bar = "#" * int(v / max_v * width)
        typer.echo(f"{k:>4}: {bar} {v}")


def _save_token(tok: str):
    TOKEN_FILE.write_text(tok)


def _load_token() -> str:
    if not TOKEN_FILE.exists():
        typer.echo("Você não está logado. Rode: cli.py login --user ... --pass ...")
        raise typer.Exit(1)
    return TOKEN_FILE.read_text().strip()


def _auth_header():
    return {"Authorization": f"Bearer {_load_token()}"}


@APP.command()
def twin_sazonalidade_chart(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/digital-twin/sazonalidade", timeout=10)
    data = r.json()
    typer.echo("== Por hora ==")
    _bar_chart({int(k): v for k, v in data["by_hour"].items()})
    typer.echo("\n== Por dia da semana (0=Mon) ==")
    _bar_chart({int(k): v for k, v in data["by_weekday"].items()})
    typer.echo("\n== Por mês ==")
    _bar_chart(data["by_month"])


@APP.command()
def ping(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/ping", timeout=5)
    typer.echo(r.json())


@APP.command()
def login(user: str = typer.Option(..., "--user"), password: str = typer.Option(..., "--pass"), api: str = API_URL_DEFAULT):
    data = {"username": user, "password": password}
    r = requests.post(f"{api}/token", data=data, timeout=10)
    if r.status_code != 200:
        typer.echo(f"Erro: {r.status_code} {r.text}")
        raise typer.Exit(1)
    _save_token(r.json()["access_token"])
    typer.echo("Login OK!")


@APP.command()
def register(username: str, password: str, api: str = API_URL_DEFAULT):
    r = requests.post(f"{api}/register", json={"username": username, "password": password}, timeout=10)
    typer.echo(r.json())


@APP.command()
def balance(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/balance", headers=_auth_header(), timeout=10)
    typer.echo(r.json())


@APP.command()
def deposit(amount: float, api: str = API_URL_DEFAULT):
    r = requests.post(f"{api}/deposit", json={"amount": amount}, headers=_auth_header(), timeout=10)
    typer.echo(r.json())


@APP.command()
def pix(to_user: str, amount: float, api: str = API_URL_DEFAULT):
    r = requests.post(f"{api}/pix", json={"to_user": to_user, "amount": amount}, headers=_auth_header(), timeout=10)
    typer.echo(r.json())


@APP.command("logs")
def get_logs(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/logs", headers=_auth_header(), timeout=10)
    typer.echo(json.dumps(r.json(), indent=2, ensure_ascii=False))


# ---- Digital Twin ----
@APP.command()
def twin_summary(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/digital-twin/summary", timeout=10)
    typer.echo(json.dumps(r.json(), indent=2, ensure_ascii=False))


@APP.command()
def twin_stats(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/digital-twin/stats", timeout=10)
    typer.echo(json.dumps(r.json(), indent=2, ensure_ascii=False))


@APP.command()
def twin_sazonalidade(api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/digital-twin/sazonalidade", timeout=10)
    typer.echo(json.dumps(r.json(), indent=2, ensure_ascii=False))


@APP.command()
def twin_shadow(username: str, api: str = API_URL_DEFAULT):
    r = requests.get(f"{api}/digital-twin/shadow/{username}", timeout=10)
    typer.echo(json.dumps(r.json(), indent=2, ensure_ascii=False))


@APP.command()
def export_logs(api_base_url: str, token: str, path: str, api: str = API_URL_DEFAULT):
    r = requests.post(f"{api}/digital-twin/export", json={"api_base_url": api_base_url, "token": token, "path": path}, timeout=10)
    typer.echo(r.json())


@APP.command()
def load_logs(path: str, api: str = API_URL_DEFAULT):
    r = requests.post(f"{api}/digital-twin/load", json={"path": path}, timeout=10)
    typer.echo(r.json())


if __name__ == "__main__":
    APP()
