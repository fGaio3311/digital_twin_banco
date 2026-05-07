"use client";

import { useEffect, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Stats = {
  total_events?: number;
  total_users?: number;
  count_by_type?: Record<string, number>;
  sum_by_type?: Record<string, number>;
  avg_by_type?: Record<string, number>;
};

export default function OverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch(`${base}/digital-twin/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Visão Geral</h2>
          <p>Indicadores essenciais do gêmeo digital.</p>
        </div>
        <div className="cards">
          <div className="card metric-card">
            <h3>Total de eventos</h3>
            <p className="value xl">{stats?.total_events ?? 0}</p>
          </div>
          <div className="card metric-card">
            <h3>Total de usuários</h3>
            <p className="value xl">{stats?.total_users ?? 0}</p>
          </div>
          <div className="card">
            <h3>Contagem por tipo</h3>
            <pre className="mono">{JSON.stringify(stats?.count_by_type ?? {}, null, 2)}</pre>
          </div>
          <div className="card">
            <h3>Volume por tipo (R$)</h3>
            <pre className="mono">{JSON.stringify(stats?.sum_by_type ?? {}, null, 2)}</pre>
          </div>
        </div>
      </section>
    </main>
  );
}
