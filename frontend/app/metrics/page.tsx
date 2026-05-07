const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function fetchHealth() {
  const res = await fetch(`${base}/health`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function MetricsPage() {
  const health = await fetchHealth();

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Observabilidade</h2>
          <p>Diagnósticos rápidos do sistema.</p>
        </div>
        <div className="cards">
          <div className="card">
            <h3>Status da API</h3>
            <p className={`value ${health ? 'ok' : 'bad'}`}>{health?.status ?? 'offline'}</p>
          </div>
          <div className="card">
            <h3>Último ping</h3>
            <p className="value">{health?.time ?? '--'}</p>
          </div>
          <div className="card">
            <h3>Métricas Prometheus</h3>
            <a href="/metrics">Abrir /metrics</a>
          </div>
        </div>
      </section>
    </main>
  );
}
