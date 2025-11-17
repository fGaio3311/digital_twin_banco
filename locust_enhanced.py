import time
import random
import json
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, STATE_RUNNING

# Metrics storage
test_start_time = None
custom_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "endpoint_stats": {},
    "response_times": [],
    "error_details": []
}

def reset_stats():
    """Reset custom statistics between test runs"""
    global test_start_time, custom_stats
    test_start_time = time.time()
    custom_stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "endpoint_stats": {},
        "response_times": [],
        "error_details": []
    }

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    reset_stats()

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    custom_stats["total_requests"] += 1

    if exception:
        custom_stats["failed_requests"] += 1
        custom_stats["error_details"].append({
            "endpoint": name,
            "error": str(exception),
            "timestamp": datetime.now().isoformat()
        })
    else:
        custom_stats["successful_requests"] += 1
        custom_stats["response_times"].append(response_time)

        if name not in custom_stats["endpoint_stats"]:
            custom_stats["endpoint_stats"][name] = {
                "count": 0,
                "success": 0,
                "failures": 0,
                "response_times": []
            }

        stats = custom_stats["endpoint_stats"][name]
        stats["count"] += 1
        if exception:
            stats["failures"] += 1
        else:
            stats["success"] += 1
            stats["response_times"].append(response_time)

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    if environment.runner.state in [STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP]:
        # Calculate test duration
        test_duration = time.time() - test_start_time

        # Calculate summary statistics
        total_reqs = custom_stats["total_requests"]
        success_rate = (custom_stats["successful_requests"] / total_reqs * 100) if total_reqs > 0 else 0

        response_times = custom_stats["response_times"]
        avg_response = sum(response_times) / len(response_times) if response_times else 0

        # Sort response times for percentiles
        if response_times:
            response_times.sort()
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
        else:
            p95 = p99 = 0

        # Create summary report
        summary = {
            "test_duration_seconds": test_duration,
            "total_requests": total_reqs,
            "requests_per_second": total_reqs / test_duration if test_duration > 0 else 0,
            "success_rate_percent": success_rate,
            "response_times": {
                "average_ms": avg_response,
                "p95_ms": p95,
                "p99_ms": p99
            },
            "endpoint_details": {}
        }

        # Add per-endpoint statistics
        for endpoint, stats in custom_stats["endpoint_stats"].items():
            if stats["response_times"]:
                stats["response_times"].sort()
                endpoint_p95 = stats["response_times"][int(len(stats["response_times"]) * 0.95)]
                endpoint_avg = sum(stats["response_times"]) / len(stats["response_times"])
            else:
                endpoint_p95 = 0
                endpoint_avg = 0

            summary["endpoint_details"][endpoint] = {
                "total_requests": stats["count"],
                "success_rate": (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0,
                "average_response_ms": endpoint_avg,
                "p95_response_ms": endpoint_p95
            }

        # Save to file
        filename = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(filename, "w") as f:
            json.dump(summary, f, indent=2)
            print(f"\nTest results saved to {filename}")

class BankUser(HttpUser):
    wait_time = between(1, 2)  # More aggressive timing for load testing

    def on_start(self):
        """Setup: Register and login a new user"""
        username = f"loadtest_{int(time.time())}_{random.randint(1000, 9999)}"
        password = "testpass123"

        # Register
        response = self.client.post("/register", json={
            "username": username,
            "password": password
        })

        if response.status_code != 200:
            print(f"Failed to register user {username}: {response.text}")
            return

        # Login
        response = self.client.post("/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.username = username
        else:
            print(f"Failed to login user {username}: {response.text}")

    @task(5)  # Higher weight for balance checks
    def check_balance(self):
        with self.client.get("/balance", headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Balance check failed: {response.text}")

    @task(3)
    def make_deposit(self):
        amount = random.randint(10, 1000)  # Random deposit amount
        with self.client.post("/deposit", json={"amount": amount}, headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Deposit failed: {response.text}")

    @task(2)
    def make_pix(self):
        amount = random.randint(5, 100)  # Random PIX amount
        target = f"user_{random.randint(1, 1000)}"  # Random target user
        with self.client.post("/pix", json={
            "to_username": target,
            "amount": amount
        }, headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"PIX transfer failed: {response.text}")

    @task(1)
    def check_transactions(self):
        with self.client.get("/transactions", headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Transaction history check failed: {response.text}")
