"""
Demonstração do Dashboard de Monitoramento do Digital Twin

Este script mostra as funcionalidades implementadas:
- Detecção de anomalias em tempo real
- Monitoramento de métricas do sistema
- Alertas automáticos
- Interface web completa
"""

import requests
import json
from datetime import datetime

def test_digital_twin_endpoints():
    """Testa todos os endpoints do Digital Twin"""

    print("🏦 TESTANDO DIGITAL TWIN - DASHBOARD DE MONITORAMENTO")
    print("=" * 60)

    # 1. Fazer login
    print("\n1. 🔐 Fazendo login...")
    try:
        login_response = requests.post(
            'http://localhost:8000/token',
            data={'username': 'test123', 'password': 'test123'}
        )

        if login_response.status_code == 200:
            token = login_response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            print("✅ Login realizado com sucesso!")
        else:
            print("❌ Erro no login")
            return
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return

    # 2. Testar endpoint de saúde do sistema
    print("\n2. 📊 Testando saúde do sistema...")
    try:
        health_response = requests.get(
            'http://localhost:8000/api/twin/health',
            headers=headers
        )

        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Dados de saúde obtidos:")
            print(f"   📈 Status: {health_data['health']['status']}")
            print(f"   💻 CPU: {health_data['health']['cpu_usage']:.1f}%")
            print(f"   🧠 Memória: {health_data['health']['memory_usage']:.1f}%")
            print(f"   👥 Usuários ativos: {health_data['health']['active_users']}")
            print(f"   💳 Transações: {health_data['transactions']['total_count']}")
        else:
            print(f"❌ Erro ao obter saúde do sistema: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    # 3. Testar detecção de anomalias
    print("\n3. 🚨 Testando detecção de anomalias...")
    try:
        anomalies_response = requests.get(
            'http://localhost:8000/api/twin/anomalies',
            headers=headers
        )

        if anomalies_response.status_code == 200:
            anomalies = anomalies_response.json()
            print(f"✅ {len(anomalies)} anomalias detectadas:")

            for anomaly in anomalies[:3]:  # Mostrar apenas as 3 primeiras
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(anomaly['severity'], '⚪')

                print(f"   {severity_emoji} {anomaly['message']}")
                print(f"      Regra: {anomaly['rule']} | Usuário: {anomaly.get('user', 'N/A')}")
        else:
            print(f"❌ Erro ao obter anomalias: {anomalies_response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    # 4. Testar métricas
    print("\n4. 📈 Testando métricas do sistema...")
    try:
        metrics_response = requests.get(
            'http://localhost:8000/api/twin/metrics',
            headers=headers
        )

        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            metrics = metrics_data.get('metrics', [])
            print(f"✅ {len(metrics)} registros de métricas disponíveis")
        else:
            print(f"❌ Erro ao obter métricas: {metrics_response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    # 5. Testar status geral
    print("\n5. ⚡ Testando status geral...")
    try:
        status_response = requests.get(
            'http://localhost:8000/api/twin/status',
            headers=headers
        )

        if status_response.status_code == 200:
            status_data = status_response.json()
            print("✅ Status do Digital Twin:")
            print(f"   📊 Status: {status_data['status']}")
            print(f"   🔧 Versão: {status_data['version']}")
            print(f"   📡 Detecção de anomalias: {'✅' if status_data['monitoring']['anomaly_detection'] else '❌'}")
            print(f"   📈 Monitoramento de performance: {'✅' if status_data['monitoring']['performance_monitoring'] else '❌'}")
            print(f"   👥 Análise comportamental: {'✅' if status_data['monitoring']['user_behavior_analysis'] else '❌'}")
            print(f"   💰 Monitoramento financeiro: {'✅' if status_data['monitoring']['financial_monitoring'] else '❌'}")
        else:
            print(f"❌ Erro ao obter status: {status_response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n" + "=" * 60)
    print("🎯 RESUMO DAS FUNCIONALIDADES IMPLEMENTADAS:")
    print("=" * 60)

    features = [
        "✅ Dashboard de monitoramento em tempo real",
        "✅ Detecção automática de anomalias",
        "✅ Alertas para transações suspeitas:",
        "   🔸 Depósitos grandes (> R$ 10.000)",
        "   🔸 PIX de alto valor (> R$ 5.000)",
        "   🔸 Alta frequência de transações",
        "✅ Monitoramento de saúde do sistema:",
        "   🔸 Uso de CPU e memória",
        "   🔸 Tempo de resposta",
        "   🔸 Taxa de erro",
        "✅ Métricas financeiras:",
        "   🔸 Volume total de transações",
        "   🔸 Distribuição por tipo (PIX, depósitos, transferências)",
        "   🔸 Atividade de usuários",
        "✅ Interface web responsiva com:",
        "   🔸 Gráficos interativos",
        "   🔸 Tabelas de histórico",
        "   🔸 Alertas visuais por severidade",
        "   🔸 Auto-refresh configurável",
        "✅ API RESTful completa para integração"
    ]

    for feature in features:
        print(feature)

    print("\n🌐 ACESSO AO SISTEMA:")
    print("=" * 30)
    print("Frontend: http://localhost:3000")
    print("Login: test123")
    print("Senha: test123")
    print("API Docs: http://localhost:8000/docs")

    print("\n📱 NAVEGAÇÃO:")
    print("- Dashboard: Visão geral financeira")
    print("- Monitoramento: Dashboard do Digital Twin 🎯")
    print("- Transações: Histórico e movimentações")
    print("- Transferir: PIX, DOC, TED")
    print("- Perfil: Dados do usuário")

if __name__ == "__main__":
    test_digital_twin_endpoints()
