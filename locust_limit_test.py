import time
import json
import random
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, STATE_RUNNING

# Shared state between users
class SharedState:
    def __init__(self):
        self.registered_users = set()
        self.user_counter = 0

    def add_user(self, username):
        self.registered_users.add(username)

    def get_random_user(self):
        if not self.registered_users:
            return None
        return random.choice(list(self.registered_users))

    def next_user_id(self):
        self.user_counter += 1
        return self.user_counter

# Initialize shared state
shared_state = SharedState()

class BankUser(HttpUser):
    wait_time = between(0.5, 2)  # Time between tasks
    abstract = True  # Base class

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = None
        self.headers = None
        self.user_id = shared_state.next_user_id()
        self.username = f"loadtest_{int(time.time())}_{self.user_id}"
        self.password = "testpass123"

    def try_auth(self, max_retries=3):
        """Attempt authentication with retries"""
        for i in range(max_retries):
            # Register
            response = self.client.post("/register", json={
                "username": self.username,
                "password": self.password
            })

            if response.status_code != 200:
                print(f"Failed to register user {self.username} (attempt {i+1}): {response.text}")
                time.sleep(1)  # Wait before retry
                continue

            # Login
            response = self.client.post("/token",
                data={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                shared_state.add_user(self.username)
                return True

            print(f"Failed to login user {self.username} (attempt {i+1}): {response.text}")
            time.sleep(1)  # Wait before retry

        return False

class PreloadUser(BankUser):
    """User class to preload some users and money"""

    def on_start(self):
        """Setup: Register, login and fund account"""
        if not self.try_auth():
            print(f"Failed to authenticate preload user {self.username}")
            return

        # Make initial deposit
        amount = 10000  # Large initial balance
        response = self.client.post(f"/deposit?amount={amount}", headers=self.headers)
        if response.status_code != 200:
            print(f"Failed initial deposit for {self.username}: {response.text}")

class TransactionUser(BankUser):
    """Main user class for load testing"""

    def on_start(self):
        """Setup: Register and login"""
        if not self.try_auth():
            print(f"Failed to authenticate transaction user {self.username}")

    def has_valid_auth(self):
        """Check if user has valid authentication"""
        return self.token is not None and self.headers is not None

    @task(5)
    def check_balance(self):
        if not self.has_valid_auth():
            return

        with self.client.get("/balance", headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Balance check failed: {response.text}")

    @task(3)
    def make_deposit(self):
        if not self.has_valid_auth():
            return

        amount = round(float(random.randint(10, 1000)), 2)
        with self.client.post(f"/deposit?amount={amount}", headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Deposit failed: {response.text}")

    @task(2)
    def make_pix(self):
        if not self.has_valid_auth():
            return

        # Get random recipient from pool of registered users
        recipient = shared_state.get_random_user()
        if not recipient or recipient == self.username:
            return  # Skip if no valid recipient

        amount = round(float(random.randint(5, 100)), 2)
        with self.client.post(f"/pix?to_username={recipient}&amount={amount}",
                            headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"PIX transfer failed: {response.text}")

    @task(1)
    def check_transactions(self):
        if not self.has_valid_auth():
            return

        with self.client.get("/transactions", headers=self.headers, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Transaction history check failed: {response.text}")
