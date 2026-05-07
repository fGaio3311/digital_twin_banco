# middleware/limiter.py
from time import time
from collections import defaultdict, deque

WINDOW = 60      # segundos
MAX_REQ = 5
_buckets = defaultdict(lambda: deque())  # ip -> timestamps

def allow(ip: str) -> bool:
    now = time()
    q = _buckets[ip]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= MAX_REQ:
        return False
    q.append(now)
    return True
