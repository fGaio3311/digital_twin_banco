"use client";

import { useEffect, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SummaryPage() {
  const [summary, setSummary] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${base}/digital-twin/summary`)
      .then((r) => r.json())
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Resumo do Twin</h2>
          <p>Estado agregado por usuário — shadow do mundo real.</p>
        </div>
        <div className="card">
          {loading ? (
            <p className="label" style={{ padding: 16 }}>Carregando...</p>
          ) : (
            <pre className="mono">{JSON.stringify(summary ?? {}, null, 2)}</pre>
          )}
        </div>
      </section>
    </main>
  );
}
