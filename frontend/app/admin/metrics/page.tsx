"use client";

import { useEffect, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Health = { status?: string; time?: string };

export default function MetricsPage() {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch(`${base}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <main className="page">
      <section className="section">
        <div className="section__header">
          <h2>Observabilidade</h2>
          <p>Diagnósticos rápidos do sistema.</p>
        </div>
        <div className="cards">
          <div className="card metric-card">
            <h3>Status da API</h3>
            <p className={`value ${health ? "ok" : "bad"}`}>
              {health?.status ?? "offline"}
            </p>
          </div>
          <div className="card metric-card">
            <h3>Último ping</h3>
            <p className="value">
              {health?.time ? new Date(health.time).toLocaleString() : "--"}
            </p>
          </div>
          <div className="card">
            <h3>Métricas Prometheus</h3>
            <p className="label" style={{ marginBottom: 8 }}>
              Endpoint Prometheus exposto pela API FastAPI.
            </p>
            <a
              href={`${base}/metrics`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#68e0ff" }}
            >
              Abrir métricas da API →
            </a>
          </div>
          <div className="card">
            <h3>API Docs</h3>
            <p className="label" style={{ marginBottom: 8 }}>Swagger UI interativo.</p>
            <a
              href={`${base}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#68e0ff" }}
            >
              Abrir Swagger →
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
