"""
Business Drivers - Volume e Performance Monitoring
Volume=8MM/dia, Picos=15k/minuto, Tempo de Resposta = 5 seg, 95%
"""
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
import psutil
import json

@dataclass
class VolumeMetrics:
    daily_volume_target: int = 8_000_000  # 8MM/dia
    peak_per_minute: int = 15_000  # 15k/minuto
    response_time_target: float = 5.0  # 5 segundos
    percentile_target: float = 95.0  # 95%

@dataclass
class PerformanceAlert:
    timestamp: datetime
    metric: str
    current_value: float
    target_value: float
    severity: str  # 'minimo', 'maximo'
    message: str

class BusinessDriversMonitor:
    def __init__(self):
        self.metrics = VolumeMetrics()
        self.current_volume = 0
        self.current_peak = 0
        self.response_times = []
        self.alerts = []
        self.monitoring = False

    def start_monitoring(self):
        """Inicia monitoramento contínuo"""
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
            self._check_volume()
            self._check_performance()
            time.sleep(60)  # Check a cada minuto

    def record_transaction(self, response_time: float):
        """Registra uma transação e seu tempo de resposta"""
        self.current_volume += 1
        self.response_times.append({
            'timestamp': datetime.now(),
            'response_time': response_time
        })

        # Mantém apenas últimos 1000 registros
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def _check_volume(self):
        """Verifica volume e picos"""
        now = datetime.now()

        # Volume diário
        daily_volume = self._get_daily_volume()
        if daily_volume > self.metrics.daily_volume_target:
            self._create_alert(
                'daily_volume',
                daily_volume,
                self.metrics.daily_volume_target,
                'maximo',
                f'Volume diário excedeu limite: {daily_volume:,} > {self.metrics.daily_volume_target:,}'
            )

        # Pico por minuto
        minute_volume = self._get_minute_volume()
        if minute_volume > self.metrics.peak_per_minute:
            self._create_alert(
                'peak_minute',
                minute_volume,
                self.metrics.peak_per_minute,
                'maximo',
                f'Pico por minuto excedido: {minute_volume:,} > {self.metrics.peak_per_minute:,}'
            )

    def _check_performance(self):
        """Verifica tempo de resposta"""
        if not self.response_times:
            return

        # Calcula percentil 95
        recent_times = [rt['response_time'] for rt in self.response_times[-100:]]
        if recent_times:
            percentile_95 = self._calculate_percentile(recent_times, 95)

            if percentile_95 > self.metrics.response_time_target:
                self._create_alert(
                    'response_time',
                    percentile_95,
                    self.metrics.response_time_target,
                    'maximo',
                    f'Tempo de resposta P95 excedido: {percentile_95:.2f}s > {self.metrics.response_time_target}s'
                )

    def _get_daily_volume(self) -> int:
        """Calcula volume das últimas 24h"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        daily_count = sum(1 for rt in self.response_times
                         if rt['timestamp'] >= yesterday)
        return daily_count

    def _get_minute_volume(self) -> int:
        """Calcula volume do último minuto"""
        now = datetime.now()
        last_minute = now - timedelta(minutes=1)

        minute_count = sum(1 for rt in self.response_times
                          if rt['timestamp'] >= last_minute)
        return minute_count

    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calcula percentil"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _create_alert(self, metric: str, current: float, target: float, severity: str, message: str):
        """Cria um alerta"""
        alert = PerformanceAlert(
            timestamp=datetime.now(),
            metric=metric,
            current_value=current,
            target_value=target,
            severity=severity,
            message=message
        )
        self.alerts.append(alert)

        # Mantém apenas últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_current_metrics(self) -> Dict:
        """Retorna métricas atuais"""
        return {
            'daily_volume': self._get_daily_volume(),
            'minute_peak': self._get_minute_volume(),
            'response_time_p95': self._get_current_p95(),
            'total_transactions': len(self.response_times),
            'active_alerts': len([a for a in self.alerts if a.timestamp >= datetime.now() - timedelta(hours=1)])
        }

    def _get_current_p95(self) -> float:
        """Calcula P95 atual"""
        if not self.response_times:
            return 0.0
        recent_times = [rt['response_time'] for rt in self.response_times[-100:]]
        return self._calculate_percentile(recent_times, 95)

    def get_alerts(self) -> List[Dict]:
        """Retorna alertas recentes"""
        return [
            {
                'timestamp': alert.timestamp.isoformat(),
                'metric': alert.metric,
                'current_value': alert.current_value,
                'target_value': alert.target_value,
                'severity': alert.severity,
                'message': alert.message
            }
            for alert in self.alerts[-20:]  # Últimos 20 alertas
        ]

    def get_current_response_time(self) -> float:
        """Retorna tempo de resposta atual médio"""
        if not self.response_times:
            return 0.0
        recent_times = list(self.response_times)[-100:]  # Últimos 100
        return sum(recent_times) / len(recent_times) if recent_times else 0.0

    def get_percentile_95(self) -> float:
        """Retorna percentil 95 dos tempos de resposta"""
        if not self.response_times:
            return 0.0
        recent_times = sorted(list(self.response_times)[-1000:])  # Últimos 1000
        if not recent_times:
            return 0.0
        idx = int(len(recent_times) * 0.95)
        return recent_times[min(idx, len(recent_times) - 1)]

    def get_metrics(self) -> Dict:
        """Retorna métricas atuais do business driver"""
        return {
            'daily_volume': {
                'current': self.current_volume,
                'target': self.metrics.daily_volume_target,
                'percentage': (self.current_volume / self.metrics.daily_volume_target) * 100
            },
            'peak_minute': {
                'current': self.current_peak,
                'target': self.metrics.peak_per_minute,
                'percentage': (self.current_peak / self.metrics.peak_per_minute) * 100
            },
            'response_time': {
                'current': self.get_current_response_time(),
                'target': self.metrics.response_time_target,
                'percentile_95': self.get_percentile_95()
            },
            'alerts_count': len(self.alerts),
            'monitoring_active': self.monitoring
        }

# Instância global para uso na aplicação
business_monitor = BusinessDriversMonitor()
