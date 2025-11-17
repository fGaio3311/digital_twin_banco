import subprocess
import time
import json
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

def run_load_test(duration_seconds=300, users=50, spawn_rate=5):
    """Run the load test with specified parameters"""
    cmd = [
        "locust",
        "-f", "locust_enhanced.py",
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "--host", "http://localhost:8000",
        "--run-time", f"{duration_seconds}s",
        "--only-summary"
    ]

    print(f"Starting load test with {users} users (spawn rate: {spawn_rate}/s) for {duration_seconds}s")
    subprocess.run(cmd)

def plot_results(results_file):
    """Create visualizations from the test results"""
    with open(results_file) as f:
        data = json.load(f)

    # Extract endpoint stats
    endpoints = list(data["endpoint_details"].keys())
    success_rates = [data["endpoint_details"][ep]["success_rate"] for ep in endpoints]
    avg_response = [data["endpoint_details"][ep]["average_response_ms"] for ep in endpoints]

    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    # Success rates
    ax1.bar(endpoints, success_rates)
    ax1.set_title('Success Rate by Endpoint')
    ax1.set_ylabel('Success Rate (%)')
    ax1.tick_params(axis='x', rotation=45)

    # Response times
    ax2.bar(endpoints, avg_response)
    ax2.set_title('Average Response Time by Endpoint')
    ax2.set_ylabel('Response Time (ms)')
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plot_file = results_file.replace('.jsonl', '_plot.png')
    plt.savefig(plot_file)
    plt.close()

    print(f"Plots saved to {plot_file}")

    # Generate summary statistics
    print("\nTest Summary:")
    print(f"Total Requests: {data['total_requests']}")
    print(f"Requests/second: {data['requests_per_second']:.2f}")
    print(f"Overall Success Rate: {data['success_rate_percent']:.2f}%")
    print(f"\nResponse Times (ms):")
    print(f"  Average: {data['response_times']['average_ms']:.2f}")
    print(f"  95th percentile: {data['response_times']['p95_ms']:.2f}")
    print(f"  99th percentile: {data['response_times']['p99_ms']:.2f}")

def main():
    # Run load test
    test_duration = 300  # 5 minutes
    num_users = 50      # 50 concurrent users
    spawn_rate = 5      # Add 5 users per second

    run_load_test(test_duration, num_users, spawn_rate)

    # Allow a moment for the results file to be written
    time.sleep(2)

    # Find the most recent results file
    from glob import glob
    result_files = glob("load_test_results_*.jsonl")
    if result_files:
        latest_file = max(result_files)
        plot_results(latest_file)
    else:
        print("No results file found!")

if __name__ == "__main__":
    main()
