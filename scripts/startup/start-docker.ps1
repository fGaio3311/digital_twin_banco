# Script PowerShell para inicializar o Digital Twin com Docker

Write-Host "🚀 Iniciando o Digital Twin System..." -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Verificar se Docker está rodando
try {
    docker info | Out-Null
    Write-Host "✅ Docker está rodando" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker não está rodando. Por favor, inicie o Docker primeiro." -ForegroundColor Red
    exit 1
}

# Parar containers existentes
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# Pergunta sobre remoção de imagens antigas
$removeImages = Read-Host "🗑️  Deseja remover imagens antigas? (y/N)"
if ($removeImages -eq "y" -or $removeImages -eq "Y") {
    Write-Host "🧹 Removendo imagens antigas..." -ForegroundColor Yellow
    docker-compose down --rmi all --volumes --remove-orphans
}

# Build e inicialização
Write-Host "🔨 Construindo e iniciando containers..." -ForegroundColor Cyan
docker-compose up --build -d

# Aguardar containers ficarem prontos
Write-Host "⏳ Aguardando containers ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status dos containers
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker-compose ps

# Verificar se tudo está funcionando
$apiStatus = try {
    Invoke-RestMethod -Uri "http://localhost:8001/ping" -TimeoutSec 5
    "OK"
} catch {
    "ERROR"
}

if ($apiStatus -eq "OK") {
    Write-Host "✅ Digital Twin System iniciado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Acesse a aplicação em:" -ForegroundColor Cyan
    Write-Host "   Frontend: http://localhost (porta 80)" -ForegroundColor White
    Write-Host "   Frontend direto: http://localhost:3000" -ForegroundColor White
    Write-Host "   API: http://localhost:8001" -ForegroundColor White
    Write-Host "   API docs: http://localhost:8001/docs" -ForegroundColor White
    Write-Host "   MQTT: localhost:1883" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Para visualizar logs em tempo real:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs -f" -ForegroundColor White
    Write-Host ""
    Write-Host "🛑 Para parar o sistema:" -ForegroundColor Red
    Write-Host "   docker-compose down" -ForegroundColor White
} else {
    Write-Host "❌ Problemas encontrados. Verificando logs..." -ForegroundColor Red
    docker-compose logs --tail=20
}
