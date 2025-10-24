"""
Requisitos Não Funcionais - RNFs Monitor
Volumetria x 3 em 99%, Picos de acesso x 2 em 99,5%
Rastreabilidade técnica 99,9%, Tempo de Resposta 500 ms, 99%
"""
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque
import psutil
import json

@dataclass
class RNFTarget:
    volumetria_multiplier: float = 3.0  # x3 volume
    volumetria_availability: float = 99.0  # 99%
    access_peak_multiplier: float = 2.0  # x2 picos
    access_peak_availability: float = 99.5  # 99.5%
    traceability_target: float = 99.9  # 99.9%
    response_time_target: float = 500.0  # 500ms
    response_time_availability: float = 99.0  # 99%

@dataclass
class RNFMetrics:
    timestamp: datetime
    volumetria_capacity_used: float  # % da capacidade
    peak_capacity_used: float  # % da capacidade de picos
    traceability_success_rate: float  # % de logs rastreáveis
    avg_response_time: float  # ms
    p99_response_time: float  # ms
    concurrent_users: int
    system_load: float

@dataclass
class RNFAlert:
    timestamp: datetime
    rnf_type: str
    current_value: float
    target_value: float
    severity: str
    message: str

class RNFMonitor:
    def __init__(self):
        self.targets = RNFTarget()
        self.metrics_history = deque(maxlen=1440)  # 24h de dados (1min interval)
        self.response_times = deque(maxlen=10000)  # Últimos 10k requests
        self.trace_logs = deque(maxlen=1000)  # Últimos 1k logs
        self.alerts = []
        self.monitoring = False
        self.base_volume_capacity = 8_000_000  # Volume base diário
        self.base_peak_capacity = 15_000  # Pico base por minuto

    def start_monitoring(self):
        """Inicia monitoramento de RNFs"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

    def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring = False

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring:
            self._collect_rnf_metrics()
            self._check_rnf_compliance()
            time.sleep(60)  # Coleta a cada minuto

    def _collect_rnf_metrics(self):
        """Coleta métricas de RNFs"""
        now = datetime.now()

        # Calcula métricas atuais
        volumetria_usage = self._calculate_volumetria_usage()
        peak_usage = self._calculate_peak_usage()
        traceability_rate = self._calculate_traceability_rate()
        avg_response = self._calculate_avg_response_time()
        p99_response = self._calculate_p99_response_time()
        concurrent_users = self._get_concurrent_users()
        system_load = psutil.cpu_percent()

        # Armazena métricas
        metrics = RNFMetrics(
            timestamp=now,
            volumetria_capacity_used=volumetria_usage,
            peak_capacity_used=peak_usage,
            traceability_success_rate=traceability_rate,
            avg_response_time=avg_response,
            p99_response_time=p99_response,
            concurrent_users=concurrent_users,
            system_load=system_load
        )

        self.metrics_history.append(metrics)

    def _calculate_volumetria_usage(self) -> float:
        """Calcula uso da capacidade volumétrica"""
        # Volume atual vs capacidade (base * 3)
        current_volume = len(self.response_times)
        max_capacity = self.base_volume_capacity * self.targets.volumetria_multiplier
        return (current_volume / max_capacity) * 100 if max_capacity > 0 else 0

    def _calculate_peak_usage(self) -> float:
        """Calcula uso da capacidade de picos"""
        # Pico do último minuto vs capacidade
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        minute_requests = sum(1 for rt in self.response_times
                            if hasattr(rt, 'timestamp') and rt.timestamp >= minute_ago)

        max_peak_capacity = self.base_peak_capacity * self.targets.access_peak_multiplier
        return (minute_requests / max_peak_capacity) * 100 if max_peak_capacity > 0 else 0

    def _calculate_traceability_rate(self) -> float:
        """Calcula taxa de rastreabilidade"""
        if not self.trace_logs:
            return 100.0

        successful_traces = sum(1 for log in self.trace_logs if log.get('traceable', False))
        return (successful_traces / len(self.trace_logs)) * 100

    def _calculate_avg_response_time(self) -> float:
        """Calcula tempo médio de resposta"""
        if not self.response_times:
            return 0.0

        recent_times = list(self.response_times)[-100:]  # Últimos 100
        return sum(rt.response_time for rt in recent_times) / len(recent_times) * 1000  # em ms

    def _calculate_p99_response_time(self) -> float:
        """Calcula percentil 99 do tempo de resposta"""
        if not self.response_times:
            return 0.0

        times = [rt.response_time * 1000 for rt in self.response_times]  # em ms
        times.sort()
        index = int(0.99 * len(times))
        return times[min(index, len(times) - 1)] if times else 0.0

    def _get_concurrent_users(self) -> int:
        """Simula número de usuários concorrentes"""
        # Em um sistema real, isso viria de sessões ativas
        return len(set(getattr(rt, 'user_id', 'anonymous') for rt in list(self.response_times)[-100:]))

    def _check_rnf_compliance(self):
        """Verifica conformidade com RNFs"""
        if not self.metrics_history:
            return

        current_metrics = self.metrics_history[-1]

        # Verifica volumetria
        if current_metrics.volumetria_capacity_used > 90:  # 90% da capacidade
            self._create_rnf_alert(
                'volumetria',
                current_metrics.volumetria_capacity_used,
                90.0,
                'warning',
                f'Volumetria próxima do limite: {current_metrics.volumetria_capacity_used:.1f}%'
            )

        # Verifica picos de acesso
        if current_metrics.peak_capacity_used > 90:
            self._create_rnf_alert(
                'peak_access',
                current_metrics.peak_capacity_used,
                90.0,
                'warning',
                f'Capacidade de picos próxima do limite: {current_metrics.peak_capacity_used:.1f}%'
            )

        # Verifica rastreabilidade
        if current_metrics.traceability_success_rate < self.targets.traceability_target:
            self._create_rnf_alert(
                'traceability',
                current_metrics.traceability_success_rate,
                self.targets.traceability_target,
                'critical',
                f'Rastreabilidade abaixo do target: {current_metrics.traceability_success_rate:.1f}%'
            )

        # Verifica tempo de resposta
        if current_metrics.p99_response_time > self.targets.response_time_target:
            self._create_rnf_alert(
                'response_time',
                current_metrics.p99_response_time,
                self.targets.response_time_target,
                'warning',
                f'Tempo de resposta P99 acima do target: {current_metrics.p99_response_time:.1f}ms'
            )

    def _create_rnf_alert(self, rnf_type: str, current: float, target: float, severity: str, message: str):
        """Cria alerta de RNF"""
        alert = RNFAlert(
            timestamp=datetime.now(),
            rnf_type=rnf_type,
            current_value=current,
            target_value=target,
            severity=severity,
            message=message
        )
        self.alerts.append(alert)

        # Mantém apenas últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def record_request(self, response_time: float, user_id: str = None, traceable: bool = True):
        """Registra uma requisição"""
        request_data = type('Request', (), {
            'timestamp': datetime.now(),
            'response_time': response_time,
            'user_id': user_id or 'anonymous'
        })()

        self.response_times.append(request_data)

        # Registra log de rastreabilidade
        self.trace_logs.append({
            'timestamp': datetime.now().isoformat(),
            'traceable': traceable,
            'user_id': user_id,
            'response_time': response_time
        })

    def get_rnf_status(self) -> Dict:
        """Retorna status atual dos RNFs"""
        if not self.metrics_history:
            return {}

        current = self.metrics_history[-1]

        return {
            'volumetria': {
                'current_usage': current.volumetria_capacity_used,
                'capacity_multiplier': self.targets.volumetria_multiplier,
                'target_availability': self.targets.volumetria_availability,
                'status': 'ok' if current.volumetria_capacity_used < 90 else 'warning'
            },
            'peak_access': {
                'current_usage': current.peak_capacity_used,
                'capacity_multiplier': self.targets.access_peak_multiplier,
                'target_availability': self.targets.access_peak_availability,
                'status': 'ok' if current.peak_capacity_used < 90 else 'warning'
            },
            'traceability': {
                'current_rate': current.traceability_success_rate,
                'target_rate': self.targets.traceability_target,
                'status': 'ok' if current.traceability_success_rate >= self.targets.traceability_target else 'critical'
            },
            'response_time': {
                'avg_time': current.avg_response_time,
                'p99_time': current.p99_response_time,
                'target_time': self.targets.response_time_target,
                'target_availability': self.targets.response_time_availability,
                'status': 'ok' if current.p99_response_time <= self.targets.response_time_target else 'warning'
            },
            'system': {
                'concurrent_users': current.concurrent_users,
                'system_load': current.system_load,
                'timestamp': current.timestamp.isoformat()
            }
        }

    def get_rnf_alerts(self) -> List[Dict]:
        """Retorna alertas de RNF"""
        return [
            {
                'timestamp': alert.timestamp.isoformat(),
                'rnf_type': alert.rnf_type,
                'current_value': alert.current_value,
                'target_value': alert.target_value,
                'severity': alert.severity,
                'message': alert.message
            }
            for alert in self.alerts[-20:]  # Últimos 20 alertas
        ]

    def get_rnf_metrics_history(self, hours: int = 24) -> List[Dict]:
        """Retorna histórico de métricas"""
        cutoff = datetime.now() - timedelta(hours=hours)

        return [
            {
                'timestamp': m.timestamp.isoformat(),
                'volumetria_usage': m.volumetria_capacity_used,
                'peak_usage': m.peak_capacity_used,
                'traceability_rate': m.traceability_success_rate,
                'avg_response_time': m.avg_response_time,
                'p99_response_time': m.p99_response_time,
                'concurrent_users': m.concurrent_users,
                'system_load': m.system_load
            }
            for m in self.metrics_history
            if m.timestamp >= cutoff
        ]

    def get_current_metrics(self) -> RNFMetrics:
        """Retorna métricas atuais simuladas"""
        import psutil

        # Simular métricas atuais
        return RNFMetrics(
            timestamp=datetime.now(),
            volumetria_capacity_used=min(psutil.cpu_percent(), 90),  # Simular uso de volumetria
            peak_capacity_used=min(psutil.virtual_memory().percent, 80),  # Simular picos
            traceability_success_rate=99.8,  # Taxa de rastreabilidade
            avg_response_time=350.0,  # Tempo médio de resposta
            p99_response_time=450.0,  # P99 tempo de resposta
            concurrent_users=len(psutil.pids()) // 10,  # Simular usuários
            system_load=psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else psutil.cpu_percent() / 100
        )

    def get_metrics(self) -> Dict:
        """Retorna métricas atuais de RNF"""
        current = self.get_current_metrics()

        return {
            'volumetria': {
                'current_usage': current.volumetria_capacity_used,
                'target_multiplier': self.targets.volumetria_multiplier,
                'availability_target': self.targets.volumetria_availability,
                'status': 'ok' if current.volumetria_capacity_used <= (100 / self.targets.volumetria_multiplier) else 'warning'
            },
            'access_peaks': {
                'current_usage': current.peak_capacity_used,
                'target_multiplier': self.targets.access_peak_multiplier,
                'availability_target': self.targets.access_peak_availability,
                'status': 'ok' if current.peak_capacity_used <= (100 / self.targets.access_peak_multiplier) else 'warning'
            },
            'traceability': {
                'current_rate': current.traceability_success_rate,
                'target_rate': self.targets.traceability_target,
                'status': 'ok' if current.traceability_success_rate >= self.targets.traceability_target else 'warning'
            },
            'response_time': {
                'avg_current': current.avg_response_time,
                'p99_current': current.p99_response_time,
                'target_time': self.targets.response_time_target,
                'availability_target': self.targets.response_time_availability,
                'status': 'ok' if current.p99_response_time <= self.targets.response_time_target else 'warning'
            },
            'system': {
                'concurrent_users': current.concurrent_users,
                'system_load': current.system_load
            },
            'alerts_count': len(self.alerts),
            'monitoring_active': self.monitoring
        }

# Instância global
rnf_monitor = RNFMonitor()
