"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${BASE}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as {
          detail?: string;
        };
        setError(data.detail ?? "Erro ao criar conta.");
        return;
      }

      router.push("/login");
    } catch {
      setError("Erro ao conectar ao servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-logo">
          <div style={{ fontSize: "3rem" }}>🏦</div>
          <h1>BancoTwin</h1>
          <p>Criar conta</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-banner">{error}</div>}

          <div className="form-field">
            <label htmlFor="u">Nome de usuário</label>
            <input
              id="u"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Escolha um usuário"
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="p">Senha</label>
            <input
              id="p"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Crie uma senha"
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? "Criando conta..." : "Criar conta →"}
          </button>
        </form>

        <p className="login-footer">
          Já tem conta? <Link href="/login">Entrar</Link>
        </p>
        <p
          className="login-footer"
          style={{ marginTop: 8, fontSize: "0.78rem", color: "#9ca3af" }}
        >
          Dica: username <strong>admin</strong> recebe acesso ao Digital Twin.
        </p>
      </div>
    </div>
  );
}
