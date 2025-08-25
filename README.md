# Bank Simulator with Digital Twin – README

> **Stack principal**: FastAPI · SQLAlchemy · PostgreSQL · MQTT (Eclipse Mosquitto) · Digital Twin (Python) · Typer CLI · Pytest

## 📑 Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Requisitos](#requisitos)
4. [.env de Exemplo](#env-de-exemplo)
5. [Instalação e Execução](#instalação-e-execução)

   * [Docker Compose](#docker-compose)
   * [Execução Local (sem Docker)](#execução-local-sem-docker)
6. [CLI (Typer)](#cli-typer)
7. [Endpoints Principais da API](#endpoints-principais-da-api)
8. [Digital Twin – Funcionalidades](#digital-twin--funcionalidades)
9. [Testes Automatizados](#testes-automatizados)

   * [Estrutura dos Testes](#estrutura-dos-testes)
   * [Cobertura OWASP](#cobertura-owasp)
   * [Como rodar](#como-rodar)
10. [Smoke Test Script](#smoke-test-script)
11. [Próximos Passos / Roadmap](#próximos-passos--roadmap)
12. [Licença](#licença)

---

## Visão Geral

Aplicação bancária mínima com **Digital Twin** acoplado. Cada evento (login, depósito, PIX, consulta de saldo) é:

* Persistido em banco (PostgreSQL)
* Logado para auditoria
* Publicado em tópico MQTT
* Reproduzido no gêmeo digital (sombra, sazonalidade, estatísticas)

Frontend web **foi descontinuado** nesta entrega; o foco é em **API + CLI** e nos requisitos de negócio do twin.

---

## Arquitetura

```
+------------------------+
|        CLI (Typer)     |
|  -> chama API REST     |
+-----------+------------+
            |
            v
+------------------------+        +----------------------+
|        FastAPI         |  --->  |  MQTT Broker (Mosq.) |
|  Auth, Transações,     |        +----------+-----------+
|  Logs, Endpoints Twin  |                   |
+-----------+------------+                   v
            |                           +----------+
            v                           |Subscriber|
+------------------------+              |(mqtt_sub)|
| PostgreSQL (Transações)|              +----------+
+------------------------+
```

* **FastAPI**: API REST com autenticação JWT.
* **DigitalTwin**: classe Python que mantém sombra/estatísticas e pode exportar/importar eventos.
* **MQTT**: eventos publicados no tópico `banco/<user>/events`.
* **mqtt\_subscriber.py**: consome eventos e aplica no twin (quando executado como serviço).
* **CLI (Typer)**: interface de linha de comando para registrar/logar/operar e consultar twin.

---

## Requisitos

* Docker & Docker Compose (para execução conteinerizada)
* Python 3.11+ (para rodar local/CLI/tests)

Bibliotecas principais (requirements.txt):

* fastapi, uvicorn
* sqlalchemy, psycopg2-binary
* pydantic-settings
* paho-mqtt
* typer, requests
* pytest, httpx

---

## .env de Exemplo

Crie um `.env` na raiz:

```dotenv
# DB
DATABASE_URL=postgresql+psycopg2://twin:twin@postgres-twin:5432/twin
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Auth
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MQTT
MQTT_BROKER_HOST=mqtt-broker
MQTT_BROKER_PORT=1883

# CORS (se usar outro cliente)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Opcional
REACT_APP_API_URL=http://localhost:8000
```

> **Nota**: O serviço `mqtt-subscriber` precisa somente de `MQTT_*`. Deixamos os demais campos como opcionais no `Settings` para não quebrar.

---

## Instalação e Execução

### Docker Compose

1. **Subir tudo**

   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```
2. **Ver logs**

   ```bash
   docker compose logs -f api mqtt-subscriber
   ```
3. **Testar API**

   ```bash
   curl http://localhost:8000/health
   ```

### Execução Local (sem Docker)

1. Crie e ative um virtualenv

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Suba o Postgres e Mosquitto localmente ou use Docker só para eles.
3. Execute API:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Execute o subscriber (opcional):

   ```bash
   python mqtt_subscriber.py
   ```

---

## CLI (Typer)

Arquivo: `cli.py`

Instalação das dependências (se não estiver em Docker):

```bash
pip install typer[all] requests
```

Exemplos:

```bash
# Registrar e logar
python cli.py register user pass
python cli.py login --user user --pass pass

# Operações bancárias
python cli.py deposit 100
python cli.py balance
python cli.py pix --to-user maria --amount 25
python cli.py logs

# Digital Twin
python cli.py twin_summary
python cli.py twin_stats
python cli.py twin_sazonalidade
python cli.py twin_shadow user
```

O token JWT fica em `.token` na raiz.

---

## Endpoints Principais da API

| Método | Rota                          | Autenticação | Descrição                           |
| ------ | ----------------------------- | ------------ | ----------------------------------- |
| GET    | `/health`                     | -            | Healthcheck                         |
| GET    | `/ping`                       | -            | Ping simples                        |
| POST   | `/register`                   | -            | Cria usuário                        |
| POST   | `/token`                      | -            | Login (OAuth2PasswordRequestForm)   |
| GET    | `/balance`                    | Bearer JWT   | Retorna saldo                       |
| POST   | `/deposit`                    | Bearer JWT   | Deposita valor                      |
| POST   | `/pix`                        | Bearer JWT   | Transfere via PIX                   |
| GET    | `/logs`                       | Bearer JWT   | Logs do usuário                     |
| GET    | `/digital-twin/summary`       | -            | Resumo do twin                      |
| GET    | `/digital-twin/stats`         | -            | Estatísticas                        |
| GET    | `/digital-twin/sazonalidade`  | -            | Sazonalidade                        |
| GET    | `/digital-twin/shadow/{user}` | -            | Sombra de um usuário                |
| POST   | `/digital-twin/export`        | -            | Exporta logs para arquivo (async)   |
| POST   | `/digital-twin/load`          | -            | Carrega logs do arquivo para o twin |

> Documentação Swagger: `http://localhost:8000/docs`

---

## Digital Twin – Funcionalidades

* **apply\_event(ev)**: Recebe eventos e atualiza estrutura interna.
* **summary()**: Retorna visão geral dos usuários/eventos.
* **stats()**: Estatísticas agregadas (quantidade, totais, médias, etc.).
* **sazonalidade()**: Distribuição temporal de eventos (ex.: por mês/dia/hora).
* **get\_shadow(username)**: Retorna o shadow (estado) de um usuário específico.
* **export\_events(username=None)**: Exporta JSON de eventos (todos ou filtrados).
* **load\_twin(path)**: Recarrega eventos de um arquivo e reconstrói o twin.

---

## Testes Automatizados

Arquivo principal: `tests/test_api.py`

### Setup

* DB de testes: `sqlite:///:memory:` para isolamento e velocidade.
* Fixture `client` sobrescreve `get_db()` para usar o banco em memória.

### Estrutura dos Testes

**Funcionais:**

* `test_register_and_login`
* `test_balance_deposit_and_pix_and_logs`

**Segurança (OWASP Top 10):**

* `test_sql_injection_login`
* `test_broken_authentication_bruteforce`
* `test_broken_object_level_authorization`
* `test_mass_assignment_on_register`
* `test_unrestricted_resource_consumption`
* `test_insufficient_logging_and_monitoring`

**Adicionais (Expandido):**

* `test_negative_or_zero_amount`
* `test_insufficient_balance_pix`
* `test_jwt_tampering`
* `test_login_error_leakage`
* `test_concurrent_deposits`
* `test_rate_limiting_login`
* `test_password_hashing`
* `test_xss_in_username`

### Cobertura OWASP

| Categoria OWASP        | Testes Correspondentes                                    |
| ---------------------- | --------------------------------------------------------- |
| Validação de Entrada   | negative\_or\_zero\_amount, sql\_injection\_login         |
| Controle de Acesso     | broken\_object\_level\_authorization, jwt\_tampering      |
| Gestão de Autenticação | broken\_authentication\_bruteforce, rate\_limiting\_login |
| Lógica de Negócio      | insufficient\_balance\_pix, concurrent\_deposits          |
| Segurança de Dados     | password\_hashing, xss\_in\_username                      |
| Resiliência / Recursos | unrestricted\_resource\_consumption                       |
| Monitoramento/Logs     | insufficient\_logging\_and\_monitoring                    |

### Como rodar

```bash
# Ambiente de dev (venv + deps instaladas)
pytest -vv

# Ou no Docker (se tiver alvo de test dentro da imagem)
docker compose run --rm api pytest -vv
```

> **Dica**: para testes de concorrência, habilite logging detalhado ou uso de `-s` para ver prints.

---

## Smoke Test Script

Arquivo: `scripts/smoke.sh`

```bash
#!/usr/bin/env bash
set -e
API=${1:-http://localhost:8000}

echo "[*] ping"
curl -s $API/ping | jq

echo "[*] register"
curl -s -X POST $API/register -H "Content-Type: application/json" \
    -d '{"username":"smoke","password":"smoke"}' | jq

echo "[*] login"
TOKEN=$(curl -s -X POST $API/token -d "username=smoke&password=smoke" | jq -r .access_token)
echo "TOKEN=$TOKEN"

echo "[*] balance"
curl -s $API/balance -H "Authorization: Bearer $TOKEN" | jq
```

Permissão de execução: `chmod +x scripts/smoke.sh`.

---

## Próximos Passos / Roadmap

* ✅ Substituir front web por CLI (feito)
* 🔒 Implementar rate limiting real (Redis ou SlowAPI)
* 🔑 MFA / 2FA em login
* 📈 Métricas de performance (Prometheus/Grafana)
* 🧪 Testes de performance/load (Locust/k6)
* 📊 Visualizações de sazonalidade (ASCII charts ou export para CSV)
* 🔐 Criptografia de dados sensíveis em repouso

---

## Licença

Definir a licença (MIT, Apache 2.0, etc.) conforme necessidades do projeto.

---

> **Contato / Contribuição**: Abra issues/PRs ou entre em contato com o responsável pelo projeto.
