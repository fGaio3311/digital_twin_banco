# syntax=docker/dockerfile:1
FROM python:3.11-slim as builder

# Cria diretório de trabalho
WORKDIR /app

# Instalar build essentials
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copia só o requirements primeiro (para cache)
COPY requirements.txt .

# Instala dependências Python em uma venv
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# Estágio final
FROM python:3.11-slim

WORKDIR /app

# Copia a venv do builder
COPY --from=builder /opt/venv /opt/venv

# Ativa a venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar somente curl para healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copia o código da API
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Expõe a porta do Uvicorn
EXPOSE 8000

# Define variáveis de ambiente para otimização Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Roda a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
