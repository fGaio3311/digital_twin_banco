@echo off
echo 🏦 INICIANDO SISTEMA BANCÁRIO DIGITAL TWIN
echo =============================================

echo.
echo 📦 Verificando dependências...
cd /d "C:\Users\gaio6\OneDrive\Documentos\digital_twin"
if not exist ".venv" (
    echo ❌ Ambiente virtual não encontrado!
    pause
    exit /b 1
)

if not exist "frontend_new\build" (
    echo 🔨 Fazendo build do frontend...
    cd frontend_new
    call npm run build
    cd ..
)

echo.
echo 🚀 Iniciando Backend (porta 8000)...
start "Backend" cmd /k "cd /d C:\Users\gaio6\OneDrive\Documentos\digital_twin && .venv\Scripts\python.exe main_simple.py"

echo.
echo ⏳ Aguardando backend inicializar...
timeout /t 3 /nobreak > nul

echo.
echo 🌐 Iniciando Frontend (porta 3000)...
start "Frontend" cmd /k "cd /d C:\Users\gaio6\OneDrive\Documentos\digital_twin\frontend_new && npx serve -s build -l 3000"

echo.
echo ⏳ Aguardando frontend inicializar...
timeout /t 5 /nobreak > nul

echo.
echo ✅ Sistema iniciado!
echo.
echo 📍 URLs de acesso:
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API Docs: http://localhost:8000/docs
echo.
echo 🔐 Credenciais de teste:
echo    Login: test123
echo    Senha: test123
echo.
echo 💡 Para parar os serviços, feche as janelas do cmd que abriram.
echo.
pause
