"use client";

import { useEffect, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${base}/digital-twin/anomalies`)
      .then((r) => r.json())
      .then(setAnomalies)
      .catch(() => setAnomalies([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="page">
      <section className="section">
        <div className="section__header split">
          <div>
            <h2>Anomalias detectadas</h2>
            <p>Últimos eventos classificados como anomalia pelo engine de IA.</p>
          </div>
          <button
            className="bank-btn ghost"
            style={{ background: "rgba(79,140,255,0.12)", color: "#68e0ff", border: "1px solid rgba(79,140,255,0.3)" }}
            onClick={() => {
              setLoading(true);
              fetch(`${base}/digital-twin/anomalies`)
                .then((r) => r.json())
                .then(setAnomalies)
                .finally(() => setLoading(false));
            }}
          >
            ↺ Atualizar
          </button>
        </div>
        <div className="card">
          {loading ? (
            <p className="label" style={{ padding: 16 }}>Carregando...</p>
          ) : (
            <pre className="mono">{JSON.stringify(anomalies, null, 2)}</pre>
          )}
        </div>
      </section>
    </main>
  );
}
