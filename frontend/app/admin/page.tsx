"use client";

import { useEffect, useMemo, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Alert = {
  timestamp: string;
  user: string;
  tipo: string;
  risk_score: number;
  details?: Record<string, unknown>;
  descricao?: string;
};

type Stats = {
  total_events?: number;
  total_users?: number;
  count_by_type?: Record<string, number>;
};

type TwinEvent = {
  timestamp: string;
  tipo: string;
  info?: Record<string, unknown>;
  descricao?: string;
  risk_score?: number;
  risk_details?: Record<string, unknown>;
};

type StreamPayload = {
  id: number;
  event: TwinEvent | null;
  stats: Stats;
  alerts: Alert[];
  timestamp: string;
};

export default function TwinDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [lastEvent, setLastEvent] = useState<TwinEvent | null>(null);
  const [connected, setConnected] = useState(false);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    let fallbackTimer: NodeJS.Timeout | undefined;

    const apply = (p: StreamPayload) => {
      setStats(p.stats);
      setAlerts(p.alerts ?? []);
      if (p.event) {
        setLastEvent(p.event);
        setFlash(true);
        setTimeout(() => setFlash(false), 900);
      }
    };

    const fetchSnapshot = async () => {
      try {
        const [ar, sr] = await Promise.all([
          fetch(`${base}/digital-twin/alerts?limit=20`),
          fetch(`${base}/digital-twin/stats`),
        ]);
        setAlerts(await ar.json());
        setStats(await sr.json());
      } catch { /* ignore */ }
    };

    const source = new EventSource(`${base}/digital-twin/stream`);
    const onMsg = (e: MessageEvent) => { setConnected(true); apply(JSON.parse(e.data)); };
    source.addEventListener("snapshot", onMsg);
    source.addEventListener("telemetry", onMsg);
    source.onerror = () => {
      setConnected(false);
      fallbackTimer = setTimeout(fetchSnapshot, 2000);
    };
    fetchSnapshot();

    return () => { source.close(); if (fallbackTimer) clearTimeout(fallbackTimer); };
  }, []);

  const typeBars = useMemo(() => {
    const counts = stats?.count_by_type ?? {};
    const max = Math.max(1, ...Object.values(counts));
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({
        type,
        count,
        width: `${Math.max(8, (count / max) * 100)}%`,
      }));
  }, [stats]);

  const maxRisk = alerts.reduce((acc, a) => Math.max(acc, a.risk_score), 0);
  const criticals = alerts.filter((a) => a.risk_score >= 70).length;

  return (
    <main className={`page ${flash ? "threat-flash" : ""}`}>
      <section className="section">
        <div className="section__header split">
          <div>
            <h2>Painel de Mitigação</h2>
            <p>Alertas, gráficos e risco do Twin em tempo real via SSE.</p>
          </div>
          <span className={`status-pill ${connected ? "ok" : "bad"}`}>
            {connected ? "stream online" : "fallback polling"}
          </span>
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
          <div className="card metric-card danger">
            <h3>Risco máximo</h3>
            <p className="value xl">{Math.round(maxRisk)}</p>
            <p className="label">{criticals} alerta(s) crítico(s)</p>
          </div>
          <div className="card metric-card">
            <h3>Última telemetria</h3>
            <p className="value">{lastEvent?.tipo ?? "--"}</p>
            <p className="label">
              {lastEvent?.descricao ?? "Aguardando eventos do banco ou da sala de simulação."}
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <h2>Gráfico de eventos</h2>
          <p>Contadores por tipo — atualizados instantaneamente.</p>
        </div>
        <div className="card chart-card">
          {typeBars.length === 0 ? (
            <p className="label">Nenhuma telemetria processada.</p>
          ) : (
            typeBars.map((item) => (
              <div className="bar-row" key={item.type}>
                <span>{item.type}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: item.width }} />
                </div>
                <strong>{item.count}</strong>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <h2>Alertas recentes</h2>
          <p>O painel pisca quando recebe telemetria de fraude, geo ou AppSec.</p>
        </div>
        <div className="cards">
          {alerts.length === 0 ? (
            <div className="card">Nenhum alerta crítico no momento.</div>
          ) : (
            alerts.map((alert, idx) => (
              <div
                className={`card alert-card ${alert.risk_score >= 70 ? "critical" : ""}`}
                key={`${alert.timestamp}-${idx}`}
              >
                <h3>{alert.tipo}</h3>
                <p className="value">Risco: {Math.round(alert.risk_score)}</p>
                <p className="label">
                  {alert.user} · {new Date(alert.timestamp).toLocaleString()}
                </p>
                <p className="label">{alert.descricao}</p>
                {alert.details && (
                  <pre className="mono compact">
                    {JSON.stringify(alert.details, null, 2)}
                  </pre>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
