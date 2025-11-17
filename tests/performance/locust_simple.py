from locust import HttpUser, task, between

class SanityUser(HttpUser):
    wait_time = between(1, 2)  # More realistic wait time

    @task
    def ping(self):
        with self.client.get("/ping", name="/ping", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
