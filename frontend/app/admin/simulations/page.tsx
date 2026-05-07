"use client";

import { useEffect, useState } from "react";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SimResult = {
  scenario: string;
  events: number;
  alerts: Array<{
    timestamp: string;
    user: string;
    tipo: string;
    risk_score: number;
    descricao?: string;
  }>;
};

type TwinEvent = {
  timestamp: string;
  tipo: string;
  descricao?: string;
  risk_score?: number;
  info?: Record<string, unknown>;
};

type StreamPayload = { id: number; event: TwinEvent | null };

const SCENARIOS = [
  {
    id: "fraude_transacional",
    title: "Simular: Fraude Transacional",
    description: "Injeta PIX de R$ 500.000 para conta recém-criada.",
  },
  {
    id: "risco_geografico",
    title: "Simular: Risco Geográfico",
    description: "Login do admin a partir da Rússia + extração de dados.",
  },
  {
    id: "appsec_exploit",
    title: "Simular: AppSec Exploit",
    description: "SQL Injection na rota /token → erro 500.",
  },
];

export default function SimulationsPage() {
  const [result, setResult] = useState<SimResult | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<TwinEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const source = new EventSource(`${base}/digital-twin/stream`);
    const onMsg = (e: MessageEvent) => {
      const p = JSON.parse(e.data) as StreamPayload;
      setConnected(true);
      if (p.event) setLiveEvents((ev) => [p.event as TwinEvent, ...ev].slice(0, 8));
    };
    source.addEventListener("snapshot", onMsg);
    source.addEventListener("telemetry", onMsg);
    source.onerror = () => setConnected(false);
    return () => source.close();
  }, []);

  const run = async (scenario: string) => {
    setLoadingId(scenario);
    try {
      const token = localStorage.getItem("dt_token");
      const res = await fetch(
        `${base}/digital-twin/simulate?scenario=${scenario}`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      setResult(await res.json());
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <main className="page">
      <section className="section">
        <div className="section__header split">
          <div>
            <h2>Simulação de Ameaças</h2>
            <p>Botões de ataque que injetam telemetria diretamente no Twin.</p>
          </div>
          <span className={`status-pill ${connected ? "ok" : "bad"}`}>
            {connected ? "dashboard reagindo em tempo real" : "stream indisponível"}
          </span>
        </div>
        <div className="cards">
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              className="card button attack-button"
              onClick={() => run(s.id)}
              disabled={loadingId !== null}
            >
              <h3>{s.title}</h3>
              <p>{s.description}</p>
              <span className="attack-state">
                {loadingId === s.id ? "Injetando..." : "Executar ataque"}
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section__header">
          <h2>Reação ao vivo</h2>
          <p>Eventos capturados pelo SSE — refletem imediatamente no Dashboard.</p>
        </div>
        <div className="cards">
          {liveEvents.length === 0 ? (
            <div className="card">Aguardando telemetria...</div>
          ) : (
            liveEvents.map((ev, i) => (
              <div className="card alert-card" key={`${ev.timestamp}-${i}`}>
                <h3>{ev.tipo}</h3>
                <p className="value">Risco: {Math.round(ev.risk_score ?? 0)}</p>
                <p className="label">{ev.descricao}</p>
                <pre className="mono compact">
                  {JSON.stringify(ev.info ?? {}, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </section>

      {result && (
        <section className="section">
          <div className="section__header">
            <h2>Resultado da injeção</h2>
            <p>Alertas gerados pelo Twin após o clique.</p>
          </div>
          <div className="card">
            <pre className="mono">{JSON.stringify(result, null, 2)}</pre>
          </div>
        </section>
      )}
    </main>
  );
}
