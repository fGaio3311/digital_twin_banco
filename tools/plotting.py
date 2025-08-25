import json
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import pathlib

LOG_PATH = pathlib.Path("metrics_log.jsonl")

from pathlib import Path
import json

LOG_PATH = Path("metrics_log.jsonl")

def load_events():
    if not LOG_PATH.exists():
        print("Aviso: metrics_log.jsonl não encontrado, retornando lista vazia.")
        return []
    events = []
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events

def plot_latency_distribution(endpoint):
    events = [e for e in load_events() if e["endpoint"] == endpoint]
    latencies = [e["latency_ms"] for e in events]
    if not latencies:
        print(f"Sem dados para {endpoint}")
        return
    plt.figure()
    plt.hist(latencies, bins=50)
    plt.xlabel("Latência (ms)")
    plt.ylabel("Contagem")
    plt.title(f"Distribuição de Latência - {endpoint}")
    plt.tight_layout()
    plt.savefig(f"latency_{endpoint.strip('/').replace('/', '_')}.png")
    print(f"Salvo latency_{endpoint.strip('/').replace('/', '_')}.png")

def plot_throughput_over_time(bin_seconds=10):
    events = load_events()
    buckets = defaultdict(int)
    for e in events:
        ts = datetime.fromisoformat(e["time"])
        key = int(ts.timestamp()) // bin_seconds * bin_seconds
        buckets[key] += 1
    times = sorted(buckets.keys())
    counts = [buckets[t] / bin_seconds for t in times]  # req/s
    plt.figure()
    plt.plot([datetime.fromtimestamp(t) for t in times], counts)
    plt.xlabel("Tempo")
    plt.ylabel("Throughput (req/s)")
    plt.title("Throughput ao longo do tempo")
    plt.tight_layout()
    plt.savefig("throughput_over_time.png")
    print("Salvo throughput_over_time.png")

def plot_error_rate():
    events = load_events()
    grouped = defaultdict(lambda: {"total":0, "fail":0})
    for e in events:
        ep = e["endpoint"]
        grouped[ep]["total"] += 1
        if not e["success"]:
            grouped[ep]["fail"] += 1
    endpoints = list(grouped.keys())
    rates = [(grouped[ep]["fail"] / grouped[ep]["total"])*100 for ep in endpoints]
    plt.figure()
    plt.bar(endpoints, rates)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Taxa de erro (%)")
    plt.title("Erro por endpoint")
    plt.tight_layout()
    plt.savefig("error_rate.png")
    print("Salvo error_rate.png")

if __name__ == "__main__":
    plot_latency_distribution("/deposit")
    plot_latency_distribution("/balance")
    plot_throughput_over_time()
    plot_error_rate()
