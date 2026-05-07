import { Suspense } from 'react';

async function fetchHealth() {
  const base = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  const res = await fetch(`${base}/health`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export default async function Home() {
  let health: { status?: string; time?: string } | null = null;
  try {
    health = await fetchHealth();
  } catch {
    health = null;
  }

  return (
    <main className="page">
      <section className="hero">
        <div className="hero__content">
          <p className="eyebrow">SecOps Bancário · Digital Twin</p>
          <h1>Monitoramento inteligente de risco e conformidade</h1>
          <p className="subtitle">
            Centralize ativos, vulnerabilidades e anomalias em tempo real com um painel moderno e auditável.
          </p>
          <div className="actions">
            <a className="btn primary" href="/docs">Abrir API Docs</a>
            <a className="btn ghost" href="/digital-twin/summary">Resumo do Twin</a>
          </div>
        </div>
        <div className="hero__card">
          <div className="card">
            <h3>Estado do sistema</h3>
            <div className="grid">
              <div>
                <p className="label">Status</p>
                <p className={`value ${health ? 'ok' : 'bad'}`}>
                  {health?.status ?? 'offline'}
                </p>
              </div>
              <div>
                <p className="label">Último ping</p>
                <p className="value">
                  {health?.time ? new Date(health.time).toLocaleString() : '--'}
                </p>
              </div>
              <div>
                <p className="label">API</p>
                <p className="value">/health</p>
              </div>
              <div>
                <p className="label">Twin</p>
                <p className="value">Ativo</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <h2>Fluxos principais</h2>
          <p>Valide rapidamente os módulos críticos do gêmeo digital.</p>
        </div>
        <div className="cards">
          <div className="card">
            <h3>Anomalias críticas</h3>
            <p>Alertas de risco classificados com severidade.</p>
            <a href="/digital-twin/anomalies">Ver anomalias</a>
          </div>
          <div className="card">
            <h3>Resumo operacional</h3>
            <p>Indicadores agregados por usuário e por tipo de evento.</p>
            <a href="/digital-twin/summary">Abrir resumo</a>
          </div>
          <div className="card">
            <h3>Telemetria</h3>
            <p>Observabilidade em tempo real do Digital Twin.</p>
            <a href="/metrics">Ver métricas</a>
          </div>
        </div>
      </section>
    </main>
  );
}
