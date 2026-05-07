const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function fetchStats() {
  const res = await fetch(`${base}/digital-twin/stats`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function OverviewPage() {
  const stats = await fetchStats();

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Visão Geral</h2>
          <p>Indicadores essenciais do gêmeo digital.</p>
        </div>
        <div className="cards">
          <div className="card">
            <h3>Total de eventos</h3>
            <p className="value">{stats?.total_events ?? 0}</p>
          </div>
          <div className="card">
            <h3>Total de usuários</h3>
            <p className="value">{stats?.total_users ?? 0}</p>
          </div>
          <div className="card">
            <h3>Tipos de evento</h3>
            <pre className="mono">{JSON.stringify(stats?.count_by_type ?? {}, null, 2)}</pre>
          </div>
        </div>
      </section>
    </main>
  );
}
