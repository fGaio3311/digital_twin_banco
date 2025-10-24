"""
Funcionalidade - Core Banking Functions
Login, Consulta Saldo/Extrato, Pix (envia/recebe)
Alertas: erros < 5%, Alarme erros > 10%
"""
import time
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json
import random

class FunctionStatus(Enum):
    AVAILABLE = "disponivel"
    DEGRADED = "degradado"
    UNAVAILABLE = "indisponivel"

class ErrorLevel(Enum):
    NORMAL = "normal"
    ALERT = "alert"  # < 5%
    ALARM = "alarm"  # > 10%

@dataclass
class FunctionMetrics:
    function_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    status: FunctionStatus = FunctionStatus.AVAILABLE
    last_check: datetime = None

@dataclass
class AvailabilityAlert:
    timestamp: datetime
    function_name: str
    error_rate: float
    level: ErrorLevel
    message: str

class FunctionalityMonitor:
    def __init__(self):
        self.functions = {
            'login': FunctionMetrics('login'),
            'consulta_saldo': FunctionMetrics('consulta_saldo'),
            'consulta_extrato': FunctionMetrics('consulta_extrato'),
            'pix_envio': FunctionMetrics('pix_envio'),
            'pix_recebimento': FunctionMetrics('pix_recebimento')
        }
        self.alerts = []
        self.monitoring = False

    def start_monitoring(self):
        """Inicia monitoramento de funcionalidades"""
        self.monitoring = True
        asyncio.create_task(self._monitor_functions())

    async def _monitor_functions(self):
        """Loop de monitoramento das funcionalidades"""
        while self.monitoring:
            for function_name in self.functions:
                await self._check_function_health(function_name)
            await asyncio.sleep(30)  # Check a cada 30 segundos

    async def _check_function_health(self, function_name: str):
        """Verifica saúde de uma funcionalidade específica"""
        metrics = self.functions[function_name]

        # Simula teste de saúde
        test_result = await self._perform_health_test(function_name)

        if test_result['success']:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        metrics.total_requests += 1
        metrics.avg_response_time = test_result['response_time']

        # Calcula taxa de erro
        if metrics.total_requests > 0:
            metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100

        # Determina status e alertas
        self._update_function_status(function_name)
        metrics.last_check = datetime.now()

    async def _perform_health_test(self, function_name: str) -> Dict:
        """Simula teste de saúde da funcionalidade"""
        start_time = time.time()

        # Simula diferentes tipos de teste baseado na função
        if function_name == 'login':
            success = await self._test_login()
        elif function_name == 'consulta_saldo':
            success = await self._test_balance_query()
        elif function_name == 'consulta_extrato':
            success = await self._test_statement_query()
        elif function_name == 'pix_envio':
            success = await self._test_pix_send()
        elif function_name == 'pix_recebimento':
            success = await self._test_pix_receive()
        else:
            success = True

        response_time = time.time() - start_time

        return {
            'success': success,
            'response_time': response_time
        }

    async def _test_login(self) -> bool:
        """Testa funcionalidade de login"""
        await asyncio.sleep(0.1)  # Simula latência
        return random.random() > 0.02  # 2% de falha

    async def _test_balance_query(self) -> bool:
        """Testa consulta de saldo"""
        await asyncio.sleep(0.05)
        return random.random() > 0.01  # 1% de falha

    async def _test_statement_query(self) -> bool:
        """Testa consulta de extrato"""
        await asyncio.sleep(0.2)
        return random.random() > 0.03  # 3% de falha

    async def _test_pix_send(self) -> bool:
        """Testa envio PIX"""
        await asyncio.sleep(0.3)
        return random.random() > 0.04  # 4% de falha

    async def _test_pix_receive(self) -> bool:
        """Testa recebimento PIX"""
        await asyncio.sleep(0.1)
        return random.random() > 0.02  # 2% de falha

    def _update_function_status(self, function_name: str):
        """Atualiza status da funcionalidade baseado na taxa de erro"""
        metrics = self.functions[function_name]
        error_rate = metrics.error_rate

        # Determina nível de alerta
        if error_rate >= 10.0:
            level = ErrorLevel.ALARM
            status = FunctionStatus.UNAVAILABLE
            message = f"ALARME: Taxa de erro crítica para {function_name}: {error_rate:.1f}%"
        elif error_rate >= 5.0:
            level = ErrorLevel.ALERT
            status = FunctionStatus.DEGRADED
            message = f"ALERTA: Taxa de erro elevada para {function_name}: {error_rate:.1f}%"
        else:
            level = ErrorLevel.NORMAL
            status = FunctionStatus.AVAILABLE
            message = f"Funcionalidade {function_name} operando normalmente: {error_rate:.1f}%"

        # Atualiza status
        if metrics.status != status:
            metrics.status = status

            # Cria alerta se necessário
            if level != ErrorLevel.NORMAL:
                self._create_availability_alert(function_name, error_rate, level, message)

    def _create_availability_alert(self, function_name: str, error_rate: float, level: ErrorLevel, message: str):
        """Cria alerta de disponibilidade"""
        alert = AvailabilityAlert(
            timestamp=datetime.now(),
            function_name=function_name,
            error_rate=error_rate,
            level=level,
            message=message
        )
        self.alerts.append(alert)

        # Mantém apenas últimos 50 alertas
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]

    def record_function_call(self, function_name: str, success: bool, response_time: float):
        """Registra chamada de funcionalidade"""
        if function_name not in self.functions:
            return

        metrics = self.functions[function_name]
        metrics.total_requests += 1

        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Atualiza tempo médio de resposta
        metrics.avg_response_time = (
            (metrics.avg_response_time * (metrics.total_requests - 1) + response_time) /
            metrics.total_requests
        )

        # Recalcula taxa de erro
        if metrics.total_requests > 0:
            metrics.error_rate = (metrics.failed_requests / metrics.total_requests) * 100

        self._update_function_status(function_name)

    def get_functionality_status(self) -> Dict:
        """Retorna status de todas as funcionalidades"""
        return {
            function_name: {
                'status': metrics.status.value,
                'error_rate': metrics.error_rate,
                'total_requests': metrics.total_requests,
                'successful_requests': metrics.successful_requests,
                'failed_requests': metrics.failed_requests,
                'avg_response_time': metrics.avg_response_time,
                'last_check': metrics.last_check.isoformat() if metrics.last_check else None
            }
            for function_name, metrics in self.functions.items()
        }

    def get_availability_alerts(self) -> List[Dict]:
        """Retorna alertas de disponibilidade"""
        return [
            {
                'timestamp': alert.timestamp.isoformat(),
                'function_name': alert.function_name,
                'error_rate': alert.error_rate,
                'level': alert.level.value,
                'message': alert.message
            }
            for alert in self.alerts[-20:]  # Últimos 20 alertas
        ]

    def get_overall_availability(self) -> Dict:
        """Calcula disponibilidade geral do sistema"""
        if not self.functions:
            return {'availability': 0.0, 'status': 'unknown'}

        total_requests = sum(m.total_requests for m in self.functions.values())
        total_successful = sum(m.successful_requests for m in self.functions.values())

        if total_requests == 0:
            availability = 100.0
        else:
            availability = (total_successful / total_requests) * 100

        # Determina status geral
        if availability >= 95.0:
            status = 'disponivel'
        elif availability >= 90.0:
            status = 'degradado'
        else:
            status = 'indisponivel'

        return {
            'availability': availability,
            'status': status,
            'total_requests': total_requests,
            'successful_requests': total_successful
        }

    def get_metrics(self) -> Dict:
        """Retorna métricas atuais de funcionalidade"""
        overall_availability = self.get_overall_availability()

        function_stats = {}
        for name, func in self.functions.items():
            function_stats[name] = {
                'total_requests': func.total_requests,
                'success_rate': ((func.successful_requests / max(func.total_requests, 1)) * 100),
                'error_rate': func.error_rate,
                'avg_response_time': func.avg_response_time,
                'status': func.status.value,
                'last_check': func.last_check.isoformat() if func.last_check else None
            }

        return {
            'overall_availability': overall_availability,
            'functions': function_stats,
            'alerts_count': len(self.alerts),
            'monitoring_active': self.monitoring
        }

# Instância global
functionality_monitor = FunctionalityMonitor()
