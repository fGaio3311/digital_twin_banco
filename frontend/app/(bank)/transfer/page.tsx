"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "../../lib/api";

type PixResult = { balance: number };

const fmt = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    v,
  );

export default function TransferPage() {
  const router = useRouter();
  const [toUser, setToUser] = useState("");
  const [amount, setAmount] = useState("");
  const [payload, setPayload] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<PixResult | null>(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!localStorage.getItem("dt_token")) {
      router.replace("/login");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess(null);

    try {
      const result = await apiFetch<PixResult>("/pix", {
        method: "POST",
        body: JSON.stringify({
          to_user: toUser,
          amount: parseFloat(amount),
          payload: payload || null,
        }),
      });
      setSuccess(result);
      setToUser("");
      setAmount("");
      setPayload("");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Erro ao realizar transferência.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bank-page">
      <Link
        href="/dashboard"
        style={{
          color: "#6b7280",
          fontSize: "0.88rem",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 24,
          textDecoration: "none",
        }}
      >
        ← Voltar
      </Link>

      <div className="bank-form">
        <h2>Transferência PIX</h2>

        {success && (
          <div className="success-banner">
            ✓ Transferência realizada! Novo saldo:{" "}
            <strong>{fmt(success.balance)}</strong>
          </div>
        )}
        {error && <div className="error-banner">⚠ {error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Destinatário (usuário)</label>
            <input
              type="text"
              value={toUser}
              onChange={(e) => setToUser(e.target.value)}
              placeholder="Nome do usuário"
              required
            />
          </div>

          <div className="form-field">
            <label>Valor</label>
            <div className="prefix">
              <span>R$</span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0,00"
                required
              />
            </div>
          </div>

          <div className="form-field">
            <label>
              Descrição{" "}
              <span style={{ fontWeight: 400, color: "#9ca3af" }}>
                (opcional — campo monitorado pelo Twin)
              </span>
            </label>
            <input
              type="text"
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder="Ex: pagamento, aluguel, ' OR 1=1 --"
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Transferindo..." : "Confirmar transferência →"}
          </button>
        </form>
      </div>
    </div>
  );
}
