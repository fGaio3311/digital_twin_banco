#!/bin/bash

# Script para inicializar o Digital Twin com Docker

echo "🚀 Iniciando o Digital Twin System..."
echo "=================================="

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down --remove-orphans

# Remover imagens antigas (opcional)
read -p "🗑️  Deseja remover imagens antigas? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removendo imagens antigas..."
    docker-compose down --rmi all --volumes --remove-orphans
fi

# Build e inicialização
echo "🔨 Construindo e iniciando containers..."
docker-compose up --build -d

# Aguardar containers ficarem saudáveis
echo "⏳ Aguardando containers ficarem prontos..."
sleep 10

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

# Verificar logs se houver problemas
if [ $? -ne 0 ]; then
    echo "❌ Problemas encontrados. Verificando logs..."
    docker-compose logs --tail=20
else
    echo "✅ Digital Twin System iniciado com sucesso!"
    echo ""
    echo "🌐 Acesse a aplicação em:"
    echo "   Frontend: http://localhost (porta 80)"
    echo "   Frontend direto: http://localhost:3000"
    echo "   API: http://localhost:8001"
    echo "   API docs: http://localhost:8001/docs"
    echo "   MQTT: localhost:1883"
    echo ""
    echo "📊 Para visualizar logs em tempo real:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Para parar o sistema:"
    echo "   docker-compose down"
fi
