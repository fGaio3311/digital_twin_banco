@echo off
REM Script para executar a aplicação completa no Windows

echo.
echo ========================================
echo 🚀 Iniciando Digital Twin + Bank Simulator
echo ========================================
echo.

REM Ativar venv
call .venv\Scripts\activate.bat

REM Iniciar a aplicação
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info

REM Se não estiver usando reload, a aplicação rodará indefinidamente
REM Acesse em: http://localhost:8000

pause
