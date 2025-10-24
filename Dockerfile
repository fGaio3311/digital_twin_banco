# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Cria diretório de trabalho
WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia só o requirements primeiro (para cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da API
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Expõe a porta do Uvicorn
EXPOSE 8001

# Roda a API com main_simple
CMD ["uvicorn", "main_simple:app", "--host", "0.0.0.0", "--port", "8001"]
