#!/bin/bash
# Script para executar a aplicação completa

echo "🚀 Iniciando Digital Twin + Bank Simulator"
echo "========================================="

# Ativar venv (se em um ambiente Unix/Linux)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Iniciar a aplicação
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info

# Se não estiver usando reload, a aplicação rodará indefinidamente
# Acesse em: http://localhost:8000
