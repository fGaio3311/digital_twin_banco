const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function fetchAnomalies() {
  const res = await fetch(`${base}/digital-twin/anomalies`, { cache: 'no-store' });
  if (!res.ok) return [];
  return res.json();
}

export default async function AnomaliesPage() {
  const anomalies = await fetchAnomalies();

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Anomalias</h2>
          <p>Últimos alertas detectados pelo gêmeo digital.</p>
        </div>
        <div className="card">
          <pre className="mono">{JSON.stringify(anomalies ?? [], null, 2)}</pre>
        </div>
      </section>
    </main>
  );
}
