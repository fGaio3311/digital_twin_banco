@echo off
echo 🏦 Iniciando Sistema Bancário Digital Twin
echo ========================================

echo.
echo 🚀 Iniciando Backend...
start /B cmd /c "cd /d C:\Users\gaio6\OneDrive\Documentos\digital_twin && C:\Users\gaio6\OneDrive\Documentos\digital_twin\.venv\Scripts\python.exe -m uvicorn main_simple:app --host 0.0.0.0 --port 8000"

echo ⏳ Aguardando backend inicializar...
timeout /t 3 /nobreak >nul

echo.
echo 📱 Iniciando Frontend...
start /B cmd /c "cd /d C:\Users\gaio6\OneDrive\Documentos\digital_twin\frontend_new && npm start"

echo.
echo ✅ Serviços iniciando...
echo 📱 Frontend: http://localhost:3000
echo 🔧 Backend: http://localhost:8000
echo.
echo ⚠️  Aguarde alguns segundos para compilação...
echo ❌ Para parar: feche as janelas do terminal
echo.
pause
