"""
Tecnologia - Technology Stack Monitor
Ferramentas, Plataformas, LLMs
Consumo de Serviços, Licenças, Contratos/SLAs
"""
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import requests
import psutil

class TechnologyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"

class LicenseStatus(Enum):
    VALID = "valid"
    EXPIRING = "expiring"  # < 30 days
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class ServiceTier(Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class TechnologyComponent:
    name: str
    category: str  # database, framework, library, platform, tool
    version: str
    status: TechnologyStatus
    last_updated: datetime
    health_check_url: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LicenseInfo:
    software_name: str
    license_type: str
    license_key: str
    holder: str
    start_date: datetime
    end_date: datetime
    status: LicenseStatus
    users_allocated: int
    users_used: int
    cost_per_month: float

@dataclass
class ServiceConsumption:
    service_name: str
    provider: str
    service_tier: ServiceTier
    usage_current: float
    usage_limit: float
    usage_unit: str  # requests, GB, hours, etc.
    cost_current: float
    cost_limit: float
    last_reset: datetime

@dataclass
class ContractSLA:
    contract_id: str
    vendor: str
    service_name: str
    sla_uptime: float  # 99.9%
    sla_response_time: float  # ms
    penalty_per_breach: float
    current_uptime: float
    current_avg_response: float
    breaches_this_month: int

class TechnologyMonitor:
    def __init__(self):
        self.technology_stack = {}
        self.licenses = {}
        self.service_consumption = {}
        self.contracts_sla = {}
        self.monitoring = False
        self.alerts = []

        # Inicializa stack tecnológico
        self._initialize_technology_stack()
        self._initialize_licenses()
        self._initialize_services()
        self._initialize_contracts()

    def _initialize_technology_stack(self):
        """Inicializa componentes tecnológicos"""
        self.technology_stack = {
            # Backend
            'python': TechnologyComponent(
                'Python', 'runtime', '3.11.2', TechnologyStatus.ACTIVE, datetime.now(),
                dependencies=['pip', 'venv']
            ),
            'fastapi': TechnologyComponent(
                'FastAPI', 'framework', '0.104.1', TechnologyStatus.ACTIVE, datetime.now(),
                health_check_url='http://localhost:8001/health'
            ),
            'uvicorn': TechnologyComponent(
                'Uvicorn', 'server', '0.24.0', TechnologyStatus.ACTIVE, datetime.now()
            ),
            'sqlalchemy': TechnologyComponent(
                'SQLAlchemy', 'orm', '2.0.23', TechnologyStatus.ACTIVE, datetime.now()
            ),
            'sqlite': TechnologyComponent(
                'SQLite', 'database', '3.42.0', TechnologyStatus.ACTIVE, datetime.now()
            ),

            # Frontend
            'react': TechnologyComponent(
                'React', 'framework', '18.2.0', TechnologyStatus.ACTIVE, datetime.now(),
                dependencies=['node', 'npm']
            ),
            'material_ui': TechnologyComponent(
                'Material-UI', 'ui_library', '5.14.19', TechnologyStatus.ACTIVE, datetime.now()
            ),
            'chartjs': TechnologyComponent(
                'Chart.js', 'visualization', '4.4.0', TechnologyStatus.ACTIVE, datetime.now()
            ),

            # Infrastructure
            'docker': TechnologyComponent(
                'Docker', 'containerization', '24.0.7', TechnologyStatus.ACTIVE, datetime.now(),
                health_check_url='http://localhost:2376/version'
            ),
            'nginx': TechnologyComponent(
                'Nginx', 'web_server', '1.24.0', TechnologyStatus.ACTIVE, datetime.now()
            ),
            'mosquitto': TechnologyComponent(
                'Eclipse Mosquitto', 'mqtt_broker', '2.0.18', TechnologyStatus.ACTIVE, datetime.now(),
                health_check_url='mqtt://localhost:1883'
            ),

            # Monitoring
            'psutil': TechnologyComponent(
                'psutil', 'monitoring', '5.9.6', TechnologyStatus.ACTIVE, datetime.now()
            )
        }

    def _initialize_licenses(self):
        """Inicializa informações de licenças"""
        now = datetime.now()

        self.licenses = {
            'windows_server': LicenseInfo(
                'Windows Server 2022', 'Commercial', 'WS22-XXXXX-XXXXX',
                'Company Corp', now - timedelta(days=365), now + timedelta(days=365),
                LicenseStatus.VALID, 50, 25, 800.0
            ),
            'visual_studio': LicenseInfo(
                'Visual Studio Professional', 'Subscription', 'VS-PROF-XXXXX',
                'Company Corp', now - timedelta(days=180), now + timedelta(days=185),
                LicenseStatus.VALID, 10, 8, 45.0
            ),
            'office365': LicenseInfo(
                'Microsoft 365 Business', 'Subscription', 'M365-BIZ-XXXXX',
                'Company Corp', now - timedelta(days=30), now + timedelta(days=335),
                LicenseStatus.VALID, 100, 87, 12.5
            )
        }

    def _initialize_services(self):
        """Inicializa consumo de serviços"""
        now = datetime.now()

        self.service_consumption = {
            'azure_compute': ServiceConsumption(
                'Azure Virtual Machines', 'Microsoft Azure', ServiceTier.PREMIUM,
                150.5, 500.0, 'hours', 75.25, 250.0, now - timedelta(days=15)
            ),
            'aws_s3': ServiceConsumption(
                'AWS S3 Storage', 'Amazon Web Services', ServiceTier.BASIC,
                25.7, 100.0, 'GB', 5.14, 25.0, now - timedelta(days=10)
            ),
            'openai_api': ServiceConsumption(
                'OpenAI GPT-4', 'OpenAI', ServiceTier.ENTERPRISE,
                1500, 10000, 'tokens', 45.0, 300.0, now - timedelta(days=5)
            ),
            'github_copilot': ServiceConsumption(
                'GitHub Copilot Business', 'GitHub', ServiceTier.PREMIUM,
                8, 10, 'users', 160.0, 200.0, now - timedelta(days=20)
            )
        }

    def _initialize_contracts(self):
        """Inicializa contratos e SLAs"""
        self.contracts_sla = {
            'azure_contract': ContractSLA(
                'AZ-2024-001', 'Microsoft Azure', 'Cloud Computing',
                99.9, 100.0, 1000.0, 99.95, 85.0, 0
            ),
            'aws_contract': ContractSLA(
                'AWS-2024-002', 'Amazon Web Services', 'Storage Services',
                99.5, 200.0, 500.0, 99.7, 150.0, 0
            ),
            'openai_contract': ContractSLA(
                'OAI-2024-003', 'OpenAI', 'AI/ML Services',
                95.0, 2000.0, 100.0, 96.5, 1800.0, 1
            )
        }

    def start_monitoring(self):
        """Inicia monitoramento tecnológico"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring:
            self._check_technology_health()
            self._check_license_expiry()
            self._monitor_service_consumption()
            self._monitor_contract_compliance()
            time.sleep(300)  # Check a cada 5 minutos

    def _check_technology_health(self):
        """Verifica saúde dos componentes tecnológicos"""
        for name, component in self.technology_stack.items():
            if component.health_check_url:
                try:
                    # Simula health check
                    if 'localhost' in component.health_check_url:
                        # Para serviços locais, verifica se a porta está respondendo
                        healthy = self._check_local_service(component.health_check_url)
                    else:
                        # Para serviços externos, faz requisição HTTP
                        response = requests.get(component.health_check_url, timeout=5)
                        healthy = response.status_code == 200

                    if not healthy and component.status == TechnologyStatus.ACTIVE:
                        self._create_technology_alert(
                            name, 'health_check_failed',
                            f'Health check failed for {component.name}'
                        )

                except Exception as e:
                    self._create_technology_alert(
                        name, 'health_check_error',
                        f'Health check error for {component.name}: {str(e)}'
                    )

    def _check_local_service(self, url: str) -> bool:
        """Verifica se serviço local está respondendo"""
        try:
            # Extrai porta da URL
            if ':' in url:
                port = int(url.split(':')[-1].split('/')[0])
                # Verifica se a porta está em uso
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return True
            return False
        except:
            return False

    def _check_license_expiry(self):
        """Verifica expiração de licenças"""
        now = datetime.now()

        for name, license_info in self.licenses.items():
            days_to_expiry = (license_info.end_date - now).days

            if days_to_expiry < 0:
                license_info.status = LicenseStatus.EXPIRED
                self._create_technology_alert(
                    name, 'license_expired',
                    f'License for {license_info.software_name} has expired'
                )
            elif days_to_expiry <= 30:
                license_info.status = LicenseStatus.EXPIRING
                self._create_technology_alert(
                    name, 'license_expiring',
                    f'License for {license_info.software_name} expires in {days_to_expiry} days'
                )
            else:
                license_info.status = LicenseStatus.VALID

    def _monitor_service_consumption(self):
        """Monitora consumo de serviços"""
        for name, service in self.service_consumption.items():
            usage_percent = (service.usage_current / service.usage_limit) * 100
            cost_percent = (service.cost_current / service.cost_limit) * 100

            if usage_percent >= 90:
                self._create_technology_alert(
                    name, 'high_usage',
                    f'High usage for {service.service_name}: {usage_percent:.1f}%'
                )

            if cost_percent >= 90:
                self._create_technology_alert(
                    name, 'high_cost',
                    f'High cost for {service.service_name}: ${service.cost_current:.2f} / ${service.cost_limit:.2f}'
                )

    def _monitor_contract_compliance(self):
        """Monitora compliance dos contratos/SLAs"""
        for contract_id, contract in self.contracts_sla.items():
            # Verifica SLA de uptime
            if contract.current_uptime < contract.sla_uptime:
                self._create_technology_alert(
                    contract_id, 'sla_breach_uptime',
                    f'Uptime SLA breach for {contract.service_name}: {contract.current_uptime:.2f}% < {contract.sla_uptime:.2f}%'
                )
                contract.breaches_this_month += 1

            # Verifica SLA de tempo de resposta
            if contract.current_avg_response > contract.sla_response_time:
                self._create_technology_alert(
                    contract_id, 'sla_breach_response',
                    f'Response time SLA breach for {contract.service_name}: {contract.current_avg_response:.1f}ms > {contract.sla_response_time:.1f}ms'
                )
                contract.breaches_this_month += 1

    def _create_technology_alert(self, component: str, alert_type: str, message: str):
        """Cria alerta tecnológico"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'type': alert_type,
            'message': message,
            'severity': self._get_alert_severity(alert_type)
        }

        self.alerts.append(alert)

        # Mantém apenas últimos 200 alertas
        if len(self.alerts) > 200:
            self.alerts = self.alerts[-200:]

    def _get_alert_severity(self, alert_type: str) -> str:
        """Determina severidade do alerta"""
        if 'expired' in alert_type or 'breach' in alert_type:
            return 'critical'
        elif 'expiring' in alert_type or 'high' in alert_type:
            return 'warning'
        else:
            return 'info'

    def update_service_usage(self, service_name: str, usage: float, cost: float):
        """Atualiza uso de serviço"""
        if service_name in self.service_consumption:
            service = self.service_consumption[service_name]
            service.usage_current = usage
            service.cost_current = cost

    def get_technology_status(self) -> Dict:
        """Retorna status da tecnologia"""
        return {
            'stack': {
                name: {
                    'name': comp.name,
                    'category': comp.category,
                    'version': comp.version,
                    'status': comp.status.value,
                    'last_updated': comp.last_updated.isoformat(),
                    'has_health_check': comp.health_check_url is not None,
                    'dependencies_count': len(comp.dependencies)
                }
                for name, comp in self.technology_stack.items()
            },
            'licenses': {
                name: {
                    'software': lic.software_name,
                    'type': lic.license_type,
                    'status': lic.status.value,
                    'days_to_expiry': (lic.end_date - datetime.now()).days,
                    'users_utilization': (lic.users_used / lic.users_allocated) * 100,
                    'monthly_cost': lic.cost_per_month
                }
                for name, lic in self.licenses.items()
            },
            'services': {
                name: {
                    'service': svc.service_name,
                    'provider': svc.provider,
                    'tier': svc.service_tier.value,
                    'usage_percent': (svc.usage_current / svc.usage_limit) * 100,
                    'cost_percent': (svc.cost_current / svc.cost_limit) * 100,
                    'usage_current': svc.usage_current,
                    'usage_limit': svc.usage_limit,
                    'usage_unit': svc.usage_unit,
                    'cost_current': svc.cost_current,
                    'cost_limit': svc.cost_limit
                }
                for name, svc in self.service_consumption.items()
            },
            'contracts': {
                contract_id: {
                    'vendor': contract.vendor,
                    'service': contract.service_name,
                    'sla_uptime': contract.sla_uptime,
                    'current_uptime': contract.current_uptime,
                    'sla_response_time': contract.sla_response_time,
                    'current_response_time': contract.current_avg_response,
                    'breaches_this_month': contract.breaches_this_month,
                    'penalty_per_breach': contract.penalty_per_breach,
                    'uptime_compliance': contract.current_uptime >= contract.sla_uptime,
                    'response_compliance': contract.current_avg_response <= contract.sla_response_time
                }
                for contract_id, contract in self.contracts_sla.items()
            }
        }

    def get_technology_alerts(self) -> List[Dict]:
        """Retorna alertas tecnológicos"""
        return self.alerts[-50:]  # Últimos 50 alertas

    def get_cost_summary(self) -> Dict:
        """Retorna resumo de custos"""
        total_license_cost = sum(lic.cost_per_month for lic in self.licenses.values())
        total_service_cost = sum(svc.cost_current for svc in self.service_consumption.values())

        return {
            'total_monthly_licenses': total_license_cost,
            'total_current_services': total_service_cost,
            'total_estimated_monthly': total_license_cost + total_service_cost,
            'breakdown': {
                'licenses': {name: lic.cost_per_month for name, lic in self.licenses.items()},
                'services': {name: svc.cost_current for name, svc in self.service_consumption.items()}
            }
        }

# Instância global
technology_monitor = TechnologyMonitor()
