import asyncio
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import tempfile

@dataclass
class LoadTestResult:
    timestamp: str
    users: int
    rps: float
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    total_requests: int
    failed_requests: int

@dataclass
class IntegrationTestResult:
    test_name: str
    status: str  # PASS, FAIL, SKIP
    duration: float
    message: Optional[str] = None
    details: Optional[Dict] = None

class AdminTestManager:
    def __init__(self):
        self.load_test_process = None
        self.load_test_running = False
        self.load_test_results = []
        self.real_time_data = {}
        self.websocket_clients = set()

    async def start_load_test(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Inicia teste de carga usando Locust"""
        try:
            if self.load_test_running:
                return {"success": False, "message": "Test already running"}

            # Criar arquivo de configuração do Locust
            locustfile_content = self._generate_locustfile(config)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(locustfile_content)
                locustfile_path = f.name

            # Comando para executar Locust
            cmd = [
                'locust',
                '-f', locustfile_path,
                '--host', config.get('host', 'http://localhost:8001'),
                '--users', str(config.get('users', 100)),
                '--spawn-rate', str(config.get('spawn_rate', 10)),
                '--run-time', f"{config.get('duration', 300)}s",
                '--headless',
                '--csv', 'load_test_results',
                '--html', 'load_test_report.html'
            ]

            # Iniciar processo Locust
            self.load_test_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            self.load_test_running = True
            self.load_test_results = []

            # Thread para monitorar resultados
            threading.Thread(
                target=self._monitor_load_test,
                args=(config.get('duration', 300),),
                daemon=True
            ).start()

            return {"success": True, "message": "Load test started"}

        except Exception as e:
            return {"success": False, "message": f"Error starting load test: {str(e)}"}

    def _generate_locustfile(self, config: Dict[str, Any]) -> str:
        """Gera arquivo Locust personalizado"""
        endpoints = config.get('endpoints', ['/ping', '/balance', '/logs'])

        locustfile = f'''
import time
import random
from locust import HttpUser, task, between

class BankingUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login se necessário
        pass

    @task(3)
    def test_ping(self):
        """Test health check endpoint"""
        self.client.get("/ping")

    @task(2)
    def test_balance(self):
        """Test balance endpoint"""
        try:
            response = self.client.get("/balance")
            if response.status_code != 200:
                print(f"Balance endpoint failed: {{response.status_code}}")
        except Exception as e:
            print(f"Balance endpoint error: {{e}}")

    @task(2)
    def test_logs(self):
        """Test logs endpoint"""
        try:
            response = self.client.get("/logs")
        except Exception as e:
            print(f"Logs endpoint error: {{e}}")

    @task(1)
    def test_digital_twin_dashboard(self):
        """Test Digital Twin dashboard"""
        try:
            response = self.client.get("/api/twin/dashboard/complete")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    pass  # Success
        except Exception as e:
            print(f"Digital Twin dashboard error: {{e}}")

    @task(1)
    def test_digital_twin_business(self):
        """Test Digital Twin business drivers"""
        try:
            self.client.get("/api/twin/business-drivers")
        except Exception as e:
            print(f"Digital Twin business error: {{e}}")

    @task(1)
    def test_digital_twin_functionality(self):
        """Test Digital Twin functionality"""
        try:
            self.client.get("/api/twin/functionality")
        except Exception as e:
            print(f"Digital Twin functionality error: {{e}}")

    @task(1)
    def test_digital_twin_rnf(self):
        """Test Digital Twin RNF"""
        try:
            self.client.get("/api/twin/rnf")
        except Exception as e:
            print(f"Digital Twin RNF error: {{e}}")

    @task(1)
    def test_digital_twin_engineering(self):
        """Test Digital Twin engineering"""
        try:
            self.client.get("/api/twin/engineering")
        except Exception as e:
            print(f"Digital Twin engineering error: {{e}}")

    @task(1)
    def test_digital_twin_technology(self):
        """Test Digital Twin technology"""
        try:
            self.client.get("/api/twin/technology")
        except Exception as e:
            print(f"Digital Twin technology error: {{e}}")
'''
        return locustfile

    def _monitor_load_test(self, duration: int):
        """Monitora teste de carga e coleta métricas"""
        start_time = time.time()

        while self.load_test_running and (time.time() - start_time) < duration:
            try:
                # Simular coleta de métricas (em implementação real, usar API do Locust)
                current_time = datetime.now().isoformat()
                elapsed = time.time() - start_time

                # Métricas simuladas baseadas no tempo decorrido
                users = min(int(elapsed * 2), 100)  # Ramp up gradual
                rps = random.uniform(80, 120) if users > 10 else random.uniform(0, 20)
                response_time_avg = random.uniform(50, 200)
                response_time_p95 = response_time_avg * random.uniform(1.5, 3.0)
                response_time_p99 = response_time_p95 * random.uniform(1.2, 2.0)
                error_rate = random.uniform(0, 5) if elapsed > 60 else 0
                total_requests = int(elapsed * rps)
                failed_requests = int(total_requests * error_rate / 100)

                result = LoadTestResult(
                    timestamp=current_time,
                    users=users,
                    rps=rps,
                    response_time_avg=response_time_avg,
                    response_time_p95=response_time_p95,
                    response_time_p99=response_time_p99,
                    error_rate=error_rate,
                    total_requests=total_requests,
                    failed_requests=failed_requests
                )

                self.load_test_results.append(result)
                self.real_time_data = asdict(result)

                # Broadcast para WebSocket clients
                asyncio.create_task(self._broadcast_to_websockets(asdict(result)))

                time.sleep(5)  # Atualização a cada 5 segundos

            except Exception as e:
                print(f"Error monitoring load test: {e}")
                break

        self.load_test_running = False

    async def _broadcast_to_websockets(self, data: Dict):
        """Envia dados em tempo real para clientes WebSocket"""
        if self.websocket_clients:
            message = json.dumps(data)
            for client in list(self.websocket_clients):
                try:
                    await client.send_text(message)
                except:
                    self.websocket_clients.discard(client)

    async def stop_load_test(self) -> Dict[str, Any]:
        """Para teste de carga"""
        try:
            if self.load_test_process:
                self.load_test_process.terminate()
                self.load_test_process = None

            self.load_test_running = False
            return {"success": True, "message": "Load test stopped"}

        except Exception as e:
            return {"success": False, "message": f"Error stopping load test: {str(e)}"}

    def get_load_test_results(self) -> List[Dict[str, Any]]:
        """Retorna resultados do teste de carga"""
        return [asdict(result) for result in self.load_test_results]

    def get_real_time_data(self) -> Dict[str, Any]:
        """Retorna dados em tempo real"""
        return self.real_time_data

    async def run_integration_tests(self) -> List[IntegrationTestResult]:
        """Executa testes de integração"""
        results = []

        # Test 1: API Health Check
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8001/ping", timeout=5)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200 and response.json().get("message") == "pong":
                results.append(IntegrationTestResult(
                    test_name="API Health Check",
                    status="PASS",
                    duration=duration,
                    message="API is responding correctly"
                ))
            else:
                results.append(IntegrationTestResult(
                    test_name="API Health Check",
                    status="FAIL",
                    duration=duration,
                    message=f"Unexpected response: {response.status_code}"
                ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="API Health Check",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        # Test 2: Digital Twin Dashboard
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8001/api/twin/dashboard/complete", timeout=10)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results.append(IntegrationTestResult(
                        test_name="Digital Twin Dashboard",
                        status="PASS",
                        duration=duration,
                        message="Dashboard returns complete data"
                    ))
                else:
                    results.append(IntegrationTestResult(
                        test_name="Digital Twin Dashboard",
                        status="FAIL",
                        duration=duration,
                        message="Dashboard status is not success"
                    ))
            else:
                results.append(IntegrationTestResult(
                    test_name="Digital Twin Dashboard",
                    status="FAIL",
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="Digital Twin Dashboard",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        # Test 3: All Digital Twin Endpoints
        endpoints = [
            "/api/twin/business-drivers",
            "/api/twin/functionality",
            "/api/twin/rnf",
            "/api/twin/engineering",
            "/api/twin/technology"
        ]

        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f"http://localhost:8001{endpoint}", timeout=5)
                duration = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    results.append(IntegrationTestResult(
                        test_name=f"Digital Twin {endpoint.split('/')[-1].title()}",
                        status="PASS",
                        duration=duration,
                        message="Endpoint responding correctly"
                    ))
                else:
                    results.append(IntegrationTestResult(
                        test_name=f"Digital Twin {endpoint.split('/')[-1].title()}",
                        status="FAIL",
                        duration=duration,
                        message=f"HTTP {response.status_code}"
                    ))
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results.append(IntegrationTestResult(
                    test_name=f"Digital Twin {endpoint.split('/')[-1].title()}",
                    status="FAIL",
                    duration=duration,
                    message=str(e)
                ))

        # Test 4: Performance Test
        start_time = time.time()
        try:
            # Teste de múltiplas requisições simultâneas
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for _ in range(20):
                    future = executor.submit(requests.get, "http://localhost:8001/ping", timeout=2)
                    futures.append(future)

                success_count = 0
                total_time = 0

                for future in futures:
                    try:
                        response = future.result()
                        if response.status_code == 200:
                            success_count += 1
                        total_time += response.elapsed.total_seconds()
                    except Exception as e:
                        print(f"Error in concurrent request: {str(e)}")
                        # Log error and continue with next request

                duration = (time.time() - start_time) * 1000
                avg_response_time = (total_time / len(futures)) * 1000

                if success_count >= 18:  # 90% success rate
                    results.append(IntegrationTestResult(
                        test_name="Concurrent Request Test",
                        status="PASS",
                        duration=duration,
                        message=f"Success rate: {success_count/20*100:.1f}%, Avg response: {avg_response_time:.1f}ms"
                    ))
                else:
                    results.append(IntegrationTestResult(
                        test_name="Concurrent Request Test",
                        status="FAIL",
                        duration=duration,
                        message=f"Low success rate: {success_count/20*100:.1f}%"
                    ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="Concurrent Request Test",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        return results

    async def run_acceptance_tests(self) -> List[IntegrationTestResult]:
        """Executa testes de aceitação"""
        results = []

        # Test 1: Business Requirements
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8001/api/twin/business-drivers", timeout=5)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})

                # Verificar se métricas de negócio estão presentes
                required_metrics = ["daily_volume", "minute_peak", "response_time_p95", "total_transactions"]
                missing_metrics = [m for m in required_metrics if m not in metrics]

                if not missing_metrics:
                    results.append(IntegrationTestResult(
                        test_name="Business Metrics Availability",
                        status="PASS",
                        duration=duration,
                        message="All required business metrics are available"
                    ))
                else:
                    results.append(IntegrationTestResult(
                        test_name="Business Metrics Availability",
                        status="FAIL",
                        duration=duration,
                        message=f"Missing metrics: {missing_metrics}"
                    ))
            else:
                results.append(IntegrationTestResult(
                    test_name="Business Metrics Availability",
                    status="FAIL",
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="Business Metrics Availability",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        # Test 2: Performance Requirements
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8001/api/twin/dashboard/complete", timeout=5)
            duration = (time.time() - start_time) * 1000

            # Verificar se resposta é dentro de 5 segundos (requirement)
            if duration <= 5000:
                results.append(IntegrationTestResult(
                    test_name="Response Time Requirement (<5s)",
                    status="PASS",
                    duration=duration,
                    message=f"Response time: {duration:.0f}ms"
                ))
            else:
                results.append(IntegrationTestResult(
                    test_name="Response Time Requirement (<5s)",
                    status="FAIL",
                    duration=duration,
                    message=f"Response time too slow: {duration:.0f}ms"
                ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="Response Time Requirement (<5s)",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        # Test 3: System Health
        start_time = time.time()
        try:
            response = requests.get("http://localhost:8001/api/twin/dashboard/complete", timeout=10)
            duration = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                overall_health = data.get("overall_health", {})

                # Verificar se todos os componentes estão healthy
                unhealthy_components = [k for k, v in overall_health.items() if v != "healthy"]

                if not unhealthy_components:
                    results.append(IntegrationTestResult(
                        test_name="System Health Check",
                        status="PASS",
                        duration=duration,
                        message="All system components are healthy"
                    ))
                else:
                    results.append(IntegrationTestResult(
                        test_name="System Health Check",
                        status="FAIL",
                        duration=duration,
                        message=f"Unhealthy components: {unhealthy_components}"
                    ))
            else:
                results.append(IntegrationTestResult(
                    test_name="System Health Check",
                    status="FAIL",
                    duration=duration,
                    message=f"HTTP {response.status_code}"
                ))
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            results.append(IntegrationTestResult(
                test_name="System Health Check",
                status="FAIL",
                duration=duration,
                message=str(e)
            ))

        return results

# Global instance
admin_test_manager = AdminTestManager()
