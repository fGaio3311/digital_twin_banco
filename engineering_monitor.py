"""
Engenharia - Infrastructure and Operations Monitor
Controle Transacional, Base de Dados, Filas, Timeout
Integrações Internas/Externas, Aferição SLAs, Logs/Threads
"""
import time
import threading
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import psutil
import json
import queue
import random

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    DOWN = "down"

class SLALevel(Enum):
    GOLD = "gold"      # 99.9%
    SILVER = "silver"  # 99.5%
    BRONZE = "bronze"  # 99.0%

@dataclass
class TransactionMetrics:
    total_transactions: int = 0
    successful_transactions: int = 0
    failed_transactions: int = 0
    timeout_transactions: int = 0
    avg_duration: float = 0.0
    active_transactions: int = 0

@dataclass
class DatabaseMetrics:
    connection_pool_size: int = 0
    active_connections: int = 0
    query_avg_time: float = 0.0
    deadlocks: int = 0
    slow_queries: int = 0
    disk_usage_percent: float = 0.0

@dataclass
class QueueMetrics:
    queue_name: str
    queue_size: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    avg_processing_time: float = 0.0
    oldest_message_age: float = 0.0

@dataclass
class IntegrationMetrics:
    integration_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_response_time: float = 0.0
    timeout_calls: int = 0
    last_success: Optional[datetime] = None
    status: ComponentStatus = ComponentStatus.HEALTHY

@dataclass
class SLAMetrics:
    service_name: str
    sla_level: SLALevel
    target_availability: float
    current_availability: float
    uptime_percentage: float
    mttr: float  # Mean Time To Recovery
    mtbf: float  # Mean Time Between Failures

@dataclass
class VitalSign:
    timestamp: datetime
    component: str
    metric_name: str
    value: float
    threshold: float
    status: ComponentStatus
    message: str

class EngineeringMonitor:
    def __init__(self):
        self.transaction_metrics = TransactionMetrics()
        self.database_metrics = DatabaseMetrics()
        self.queue_metrics = {}
        self.integration_metrics = {}
        self.sla_metrics = {}
        self.vital_signs = []
        self.system_logs = []
        self.thread_metrics = {}
        self.monitoring = False

        # Inicializa componentes
        self._initialize_components()

    def _initialize_components(self):
        """Inicializa métricas dos componentes"""
        # Filas
        self.queue_metrics = {
            'payment_queue': QueueMetrics('payment_queue'),
            'notification_queue': QueueMetrics('notification_queue'),
            'audit_queue': QueueMetrics('audit_queue')
        }

        # Integrações
        self.integration_metrics = {
            'bank_core': IntegrationMetrics('bank_core'),
            'pix_bacen': IntegrationMetrics('pix_bacen'),
            'notification_service': IntegrationMetrics('notification_service'),
            'audit_service': IntegrationMetrics('audit_service')
        }

        # SLAs
        self.sla_metrics = {
            'api_gateway': SLAMetrics('api_gateway', SLALevel.GOLD, 99.9, 0.0, 0.0, 0.0, 0.0),
            'payment_processing': SLAMetrics('payment_processing', SLALevel.SILVER, 99.5, 0.0, 0.0, 0.0, 0.0),
            'user_management': SLAMetrics('user_management', SLALevel.BRONZE, 99.0, 0.0, 0.0, 0.0, 0.0)
        }

    def start_monitoring(self):
        """Inicia monitoramento de engenharia"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring:
            self._collect_transaction_metrics()
            self._collect_database_metrics()
            self._collect_queue_metrics()
            self._collect_integration_metrics()
            self._collect_thread_metrics()
            self._calculate_sla_metrics()
            self._check_vital_signs()
            time.sleep(30)  # Coleta a cada 30 segundos

    def _collect_transaction_metrics(self):
        """Coleta métricas transacionais"""
        # Simula coleta de métricas transacionais
        self.transaction_metrics.active_transactions = random.randint(10, 100)

    def _collect_database_metrics(self):
        """Coleta métricas do banco de dados"""
        # Simula métricas de banco
        self.database_metrics.connection_pool_size = 20
        self.database_metrics.active_connections = random.randint(5, 18)
        self.database_metrics.query_avg_time = random.uniform(50, 200)  # ms
        self.database_metrics.disk_usage_percent = psutil.disk_usage('/').percent

    def _collect_queue_metrics(self):
        """Coleta métricas das filas"""
        for queue_name, metrics in self.queue_metrics.items():
            metrics.queue_size = random.randint(0, 50)
            metrics.avg_processing_time = random.uniform(100, 500)  # ms
            metrics.oldest_message_age = random.uniform(0, 300)  # seconds

    def _collect_integration_metrics(self):
        """Coleta métricas das integrações"""
        for integration_name, metrics in self.integration_metrics.items():
            # Simula chamada de integração
            success_rate = random.uniform(0.95, 1.0)
            metrics.avg_response_time = random.uniform(100, 1000)  # ms

            if success_rate > 0.99:
                metrics.status = ComponentStatus.HEALTHY
            elif success_rate > 0.95:
                metrics.status = ComponentStatus.DEGRADED
            else:
                metrics.status = ComponentStatus.CRITICAL

    def _collect_thread_metrics(self):
        """Coleta métricas de threads"""
        self.thread_metrics = {
            'total_threads': threading.active_count(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
            'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
        }

    def _calculate_sla_metrics(self):
        """Calcula métricas de SLA"""
        for service_name, sla in self.sla_metrics.items():
            # Simula cálculo de disponibilidade
            sla.current_availability = random.uniform(99.0, 99.99)
            sla.uptime_percentage = sla.current_availability
            sla.mttr = random.uniform(5, 30)  # minutes
            sla.mtbf = random.uniform(720, 8760)  # hours

    def _check_vital_signs(self):
        """Verifica sinais vitais do sistema"""
        now = datetime.now()

        # CPU
        cpu_usage = psutil.cpu_percent()
        cpu_status = self._get_threshold_status(cpu_usage, 80, 95)
        self._add_vital_sign(now, 'system', 'cpu_usage', cpu_usage, 80, cpu_status,
                           f'CPU usage: {cpu_usage:.1f}%')

        # Memória
        memory_usage = psutil.virtual_memory().percent
        memory_status = self._get_threshold_status(memory_usage, 85, 95)
        self._add_vital_sign(now, 'system', 'memory_usage', memory_usage, 85, memory_status,
                           f'Memory usage: {memory_usage:.1f}%')

        # Disco
        disk_usage = psutil.disk_usage('/').percent
        disk_status = self._get_threshold_status(disk_usage, 90, 98)
        self._add_vital_sign(now, 'system', 'disk_usage', disk_usage, 90, disk_status,
                           f'Disk usage: {disk_usage:.1f}%')

        # Conexões de banco
        db_connections = self.database_metrics.active_connections
        db_status = self._get_threshold_status(db_connections, 15, 18)
        self._add_vital_sign(now, 'database', 'active_connections', db_connections, 15, db_status,
                           f'DB connections: {db_connections}')

    def _get_threshold_status(self, value: float, warning_threshold: float, critical_threshold: float) -> ComponentStatus:
        """Determina status baseado em thresholds"""
        if value >= critical_threshold:
            return ComponentStatus.CRITICAL
        elif value >= warning_threshold:
            return ComponentStatus.DEGRADED
        else:
            return ComponentStatus.HEALTHY

    def _add_vital_sign(self, timestamp: datetime, component: str, metric_name: str,
                       value: float, threshold: float, status: ComponentStatus, message: str):
        """Adiciona sinal vital"""
        vital_sign = VitalSign(
            timestamp=timestamp,
            component=component,
            metric_name=metric_name,
            value=value,
            threshold=threshold,
            status=status,
            message=message
        )

        self.vital_signs.append(vital_sign)

        # Mantém apenas últimos 1000 sinais
        if len(self.vital_signs) > 1000:
            self.vital_signs = self.vital_signs[-1000:]

    def record_transaction(self, duration: float, success: bool, timeout: bool = False):
        """Registra uma transação"""
        self.transaction_metrics.total_transactions += 1

        if timeout:
            self.transaction_metrics.timeout_transactions += 1
        elif success:
            self.transaction_metrics.successful_transactions += 1
        else:
            self.transaction_metrics.failed_transactions += 1

        # Atualiza tempo médio
        total = self.transaction_metrics.total_transactions
        current_avg = self.transaction_metrics.avg_duration
        self.transaction_metrics.avg_duration = ((current_avg * (total - 1)) + duration) / total

    def record_integration_call(self, integration_name: str, response_time: float,
                               success: bool, timeout: bool = False):
        """Registra chamada de integração"""
        if integration_name not in self.integration_metrics:
            return

        metrics = self.integration_metrics[integration_name]
        metrics.total_calls += 1

        if timeout:
            metrics.timeout_calls += 1
        elif success:
            metrics.successful_calls += 1
            metrics.last_success = datetime.now()
        else:
            metrics.failed_calls += 1

        # Atualiza tempo médio
        total = metrics.total_calls
        current_avg = metrics.avg_response_time
        metrics.avg_response_time = ((current_avg * (total - 1)) + response_time) / total

    def add_system_log(self, level: str, component: str, message: str, details: Dict = None):
        """Adiciona log do sistema"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'component': component,
            'message': message,
            'details': details or {}
        }

        self.system_logs.append(log_entry)

        # Mantém apenas últimos 10000 logs
        if len(self.system_logs) > 10000:
            self.system_logs = self.system_logs[-10000:]

    def get_engineering_status(self) -> Dict:
        """Retorna status geral de engenharia"""
        return {
            'transactions': {
                'total': self.transaction_metrics.total_transactions,
                'successful': self.transaction_metrics.successful_transactions,
                'failed': self.transaction_metrics.failed_transactions,
                'timeout': self.transaction_metrics.timeout_transactions,
                'active': self.transaction_metrics.active_transactions,
                'avg_duration': self.transaction_metrics.avg_duration,
                'success_rate': (self.transaction_metrics.successful_transactions /
                               max(self.transaction_metrics.total_transactions, 1)) * 100
            },
            'database': {
                'pool_size': self.database_metrics.connection_pool_size,
                'active_connections': self.database_metrics.active_connections,
                'query_avg_time': self.database_metrics.query_avg_time,
                'deadlocks': self.database_metrics.deadlocks,
                'slow_queries': self.database_metrics.slow_queries,
                'disk_usage': self.database_metrics.disk_usage_percent
            },
            'queues': {
                name: {
                    'size': metrics.queue_size,
                    'processed': metrics.messages_processed,
                    'failed': metrics.messages_failed,
                    'avg_processing_time': metrics.avg_processing_time,
                    'oldest_message_age': metrics.oldest_message_age
                }
                for name, metrics in self.queue_metrics.items()
            },
            'integrations': {
                name: {
                    'total_calls': metrics.total_calls,
                    'successful_calls': metrics.successful_calls,
                    'failed_calls': metrics.failed_calls,
                    'timeout_calls': metrics.timeout_calls,
                    'avg_response_time': metrics.avg_response_time,
                    'status': metrics.status.value,
                    'last_success': metrics.last_success.isoformat() if metrics.last_success else None,
                    'success_rate': (metrics.successful_calls / max(metrics.total_calls, 1)) * 100
                }
                for name, metrics in self.integration_metrics.items()
            },
            'threads': self.thread_metrics
        }

    def get_sla_status(self) -> Dict:
        """Retorna status dos SLAs"""
        return {
            name: {
                'sla_level': metrics.sla_level.value,
                'target_availability': metrics.target_availability,
                'current_availability': metrics.current_availability,
                'uptime_percentage': metrics.uptime_percentage,
                'mttr_minutes': metrics.mttr,
                'mtbf_hours': metrics.mtbf,
                'compliance': 'compliant' if metrics.current_availability >= metrics.target_availability else 'non_compliant'
            }
            for name, metrics in self.sla_metrics.items()
        }

    def get_vital_signs(self, hours: int = 1) -> List[Dict]:
        """Retorna sinais vitais recentes"""
        cutoff = datetime.now() - timedelta(hours=hours)

        return [
            {
                'timestamp': vs.timestamp.isoformat(),
                'component': vs.component,
                'metric_name': vs.metric_name,
                'value': vs.value,
                'threshold': vs.threshold,
                'status': vs.status.value,
                'message': vs.message
            }
            for vs in self.vital_signs
            if vs.timestamp >= cutoff
        ]

    def get_system_logs(self, level: str = None, component: str = None, hours: int = 1) -> List[Dict]:
        """Retorna logs do sistema"""
        cutoff = datetime.now() - timedelta(hours=hours)

        filtered_logs = []
        for log in self.system_logs:
            log_time = datetime.fromisoformat(log['timestamp'])
            if log_time >= cutoff:
                if level and log['level'] != level:
                    continue
                if component and log['component'] != component:
                    continue
                filtered_logs.append(log)

        return filtered_logs[-100:]  # Últimos 100 logs

    def get_metrics(self) -> Dict:
        """Retorna métricas atuais de engenharia"""
        status = self.get_engineering_status()
        sla_status = self.get_sla_status()

        return {
            'transaction_control': {
                'total': self.transaction_metrics.total_transactions,
                'successful': self.transaction_metrics.successful_transactions,
                'failed': self.transaction_metrics.failed_transactions,
                'timeout': self.transaction_metrics.timeout_transactions,
                'active': self.transaction_metrics.active_transactions,
                'avg_duration': self.transaction_metrics.avg_duration
            },
            'database': {
                'pool_size': self.database_metrics.connection_pool_size,
                'active_connections': self.database_metrics.active_connections,
                'avg_query_time': self.database_metrics.query_avg_time,
                'deadlocks': self.database_metrics.deadlocks,
                'slow_queries': self.database_metrics.slow_queries,
                'disk_usage': self.database_metrics.disk_usage_percent
            },
            'queues': {name: queue.queue_size for name, queue in self.queue_metrics.items()},
            'integrations': {name: int.status.value for name, int in self.integrations.items()},
            'sla_status': sla_status,
            'overall_status': status.get('overall_status', 'unknown'),
            'alerts_count': len(self.alerts),
            'monitoring_active': self.monitoring
        }

# Instância global
engineering_monitor = EngineeringMonitor()
