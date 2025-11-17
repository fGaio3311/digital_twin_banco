import requests
import time
import statistics

# Test the PostgreSQL instance
url = "http://localhost:8000/ping"
response_times = []
errors = 0
successes = 0

print("Testing PostgreSQL performance...")
print(f"URL: {url}")
print("Running 100 requests...\n")

for i in range(100):
    try:
        start = time.time()
        response = requests.get(url, timeout=5)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        if response.status_code == 200:
            response_times.append(elapsed)
            successes += 1
            print(f"Request {i+1}: {elapsed:.2f}ms - OK")
        else:
            errors += 1
            print(f"Request {i+1}: Status {response.status_code} - FAIL")
    except requests.exceptions.Timeout:
        errors += 1
        print(f"Request {i+1}: TIMEOUT - FAIL")
    except Exception as e:
        errors += 1
        print(f"Request {i+1}: {str(e)} - FAIL")

print(f"\n{'='*50}")
print(f"Results Summary:")
print(f"Successful Requests: {successes}")
print(f"Failed Requests: {errors}")
print(f"Success Rate: {(successes/100)*100:.2f}%")

if response_times:
    print(f"\nResponse Time Statistics (ms):")
    print(f"Average: {statistics.mean(response_times):.2f}ms")
    print(f"Median: {statistics.median(response_times):.2f}ms")
    print(f"Min: {min(response_times):.2f}ms")
    print(f"Max: {max(response_times):.2f}ms")
    print(f"Stdev: {statistics.stdev(response_times) if len(response_times) > 1 else 0:.2f}ms")
