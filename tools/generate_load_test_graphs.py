import pandas as pd
import matplotlib.pyplot as plt

# Carregar os dados do teste de carga
requests_data = pd.read_csv("load_test_results_stats.csv")
failures_data = pd.read_csv("load_test_results_failures.csv")

# Gráfico de Throughput
plt.figure(figsize=(10, 6))
requests_data.groupby("Name")["Request Count"].sum().plot(kind="bar", color="skyblue")
plt.title("Throughput por Endpoint")
plt.xlabel("Endpoint")
plt.ylabel("Número de Requisições")
plt.tight_layout()
plt.savefig("throughput_per_endpoint.png")

# Gráfico de Latência
plt.figure(figsize=(10, 6))
requests_data.groupby("Name")["Average Response Time"].mean().plot(kind="bar", color="orange")
plt.title("Latência Média por Endpoint")
plt.xlabel("Endpoint")
plt.ylabel("Latência Média (ms)")
plt.tight_layout()
plt.savefig("latency_per_endpoint.png")

# Gráfico de Taxa de Erro
plt.figure(figsize=(10, 6))
failures_data.groupby("Method")["Occurrences"].sum().plot(kind="bar", color="red")
plt.title("Taxa de Erro por Método")
plt.xlabel("Método")
plt.ylabel("Número de Falhas")
plt.tight_layout()
plt.savefig("error_rate_per_method.png")

print("Gráficos gerados: throughput_per_endpoint.png, latency_per_endpoint.png, error_rate_per_method.png")
