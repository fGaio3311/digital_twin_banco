const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function fetchSummary() {
  const res = await fetch(`${base}/digital-twin/summary`, { cache: 'no-store' });
  if (!res.ok) return null;
  return res.json();
}

export default async function SummaryPage() {
  const summary = await fetchSummary();

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Resumo do Twin</h2>
          <p>Estado agregado por usuário.</p>
        </div>
        <div className="card">
          <pre className="mono">{JSON.stringify(summary ?? {}, null, 2)}</pre>
        </div>
      </section>
    </main>
  );
}
