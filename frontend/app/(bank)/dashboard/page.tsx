"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "../../lib/api";
import { clearAuth, getUsername } from "../../lib/auth";

type UserData = { username: string; balance: number; role: string };
type Txn = {
  id: number;
  type: string;
  amount: number;
  timestamp: string | null;
};

const fmt = (v: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(v);

const fmtDate = (ts: string | null) => {
  if (!ts) return "--";
  return new Date(ts).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const TXN_ICON: Record<string, string> = {
  deposit: "↑",
  pix: "↓",
  pix_received: "↓",
};
const TXN_LABEL: Record<string, string> = {
  deposit: "Depósito",
  pix: "PIX enviado",
  pix_received: "PIX recebido",
};

export default function BankDashboard() {
  const router = useRouter();
  const [userData, setUserData] = useState<UserData | null>(null);
  const [txns, setTxns] = useState<Txn[]>([]);
  const [loading, setLoading] = useState(true);
  const [depositAmount, setDepositAmount] = useState("");
  const [depositStatus, setDepositStatus] = useState("");

  useEffect(() => {
    if (!localStorage.getItem("dt_token")) {
      router.replace("/login");
      return;
    }
    Promise.all([
      apiFetch<UserData>("/user/me"),
      apiFetch<Txn[]>("/bank/transactions?limit=5"),
    ])
      .then(([user, t]) => {
        setUserData(user);
        setTxns(t);
      })
      .catch(() => {
        clearAuth();
        router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    const amount = parseFloat(depositAmount);
    if (!amount || amount <= 0) return;
    try {
      const result = await apiFetch<{ balance: number }>("/deposit", {
        method: "POST",
        body: JSON.stringify({ amount }),
      });
      setUserData((prev) =>
        prev ? { ...prev, balance: result.balance } : prev,
      );
      setDepositStatus(`✓ Depósito de ${fmt(amount)} realizado!`);
      setDepositAmount("");
      const t = await apiFetch<Txn[]>("/bank/transactions?limit=5");
      setTxns(t);
    } catch {
      setDepositStatus("⚠ Erro ao depositar.");
    }
    setTimeout(() => setDepositStatus(""), 4000);
  };

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
        <p style={{ color: "#6b7280" }}>Carregando...</p>
      </div>
    );
  }

  return (
    <div className="bank-page">
      <div style={{ maxWidth: 660 }}>
        <p style={{ color: "#6b7280", marginBottom: 24 }}>
          Olá, <strong>{userData?.username ?? getUsername()}</strong>! Bem-vindo
          ao BancoTwin.
        </p>

        {/* Balance */}
        <div className="bank-balance-card">
          <p className="bank-balance-label">Saldo disponível</p>
          <p className="bank-balance-amount">{fmt(userData?.balance ?? 0)}</p>
          <div className="bank-actions">
            <Link href="/transfer" className="bank-btn primary">
              ⇄ Transferir / PIX
            </Link>
            <Link href="/statement" className="bank-btn ghost">
              ≡ Ver extrato
            </Link>
          </div>
        </div>

        {/* Quick Deposit */}
        <div
          className="bank-card"
          style={{ padding: "20px 24px", marginBottom: 24 }}
        >
          <p className="bank-section-title" style={{ marginBottom: 12 }}>
            Depósito rápido
          </p>
          {depositStatus && (
            <div
              className={
                depositStatus.startsWith("✓")
                  ? "success-banner"
                  : "error-banner"
              }
              style={{ marginBottom: 12 }}
            >
              {depositStatus}
            </div>
          )}
          <form
            onSubmit={handleDeposit}
            style={{ display: "flex", gap: 10, alignItems: "flex-end" }}
          >
            <div className="form-field" style={{ flex: 1, marginBottom: 0 }}>
              <div className="prefix">
                <span>R$</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0,00"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              className="submit-btn"
              style={{ width: "auto", padding: "12px 24px", marginTop: 0 }}
            >
              Depositar
            </button>
          </form>
        </div>

        {/* Transactions */}
        <p className="bank-section-title">Últimas movimentações</p>
        <div className="bank-card">
          {txns.length === 0 ? (
            <div className="bank-txn">
              <p style={{ color: "#9ca3af", fontSize: "0.9rem" }}>
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
                    {TXN_ICON[t.type] ?? "·"}
                  </div>
                  <div className="bank-txn__info">
                    <p className="bank-txn__name">
                      {TXN_LABEL[t.type] ?? t.type}
                    </p>
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
