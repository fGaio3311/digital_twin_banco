"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { clearAuth } from "../../lib/auth";

type Txn = {
  id: number;
  type: string;
  amount: number;
  timestamp: string | null;
};

const fmt = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    v,
  );

const fmtDate = (ts: string | null) => {
  if (!ts) return "--";
  return new Date(ts).toLocaleString("pt-BR");
};

const LABEL: Record<string, string> = {
  deposit: "Depósito",
  pix: "PIX enviado",
  pix_received: "PIX recebido",
};
const ICON: Record<string, string> = {
  deposit: "↑",
  pix: "↓",
  pix_received: "↓",
};

export default function StatementPage() {
  const router = useRouter();
  const [txns, setTxns] = useState<Txn[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("dt_token")) {
      router.replace("/login");
      return;
    }
    apiFetch<Txn[]>("/bank/transactions?limit=100")
      .then(setTxns)
      .catch(() => {
        clearAuth();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <div
        className="bank-page"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "60vh",
        }}
      >
        <p style={{ color: "#6b7280" }}>Carregando extrato...</p>
      </div>
    );
  }

  return (
    <div className="bank-page">
      <div style={{ maxWidth: 660 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 24,
          }}
        >
          <div>
            <h1
              style={{ fontSize: "1.5rem", fontWeight: 800, color: "#111827" }}
            >
              Extrato
            </h1>
            <p style={{ color: "#6b7280", marginTop: 4 }}>
              {txns.length} movimentações
            </p>
          </div>
          <Link
            href="/dashboard"
            style={{ color: "#1a56db", fontSize: "0.88rem" }}
          >
            ← Voltar
          </Link>
        </div>

        <div className="bank-card">
          {txns.length === 0 ? (
            <div className="bank-txn">
              <p style={{ color: "#9ca3af" }}>
                Nenhuma movimentação encontrada.
              </p>
            </div>
          ) : (
            txns.map((t) => {
              const isCredit =
                t.type === "deposit" || t.type === "pix_received";
              return (
                <div className="bank-txn" key={t.id}>
                  <div className={`bank-txn__icon ${t.type}`}>
                    {ICON[t.type] ?? "·"}
                  </div>
                  <div className="bank-txn__info">
                    <p className="bank-txn__name">{LABEL[t.type] ?? t.type}</p>
                    <p className="bank-txn__date">{fmtDate(t.timestamp)}</p>
                  </div>
                  <p
                    className={`bank-txn__amount ${isCredit ? "credit" : "debit"}`}
                  >
                    {isCredit ? "+" : "-"}
                    {fmt(t.amount)}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
