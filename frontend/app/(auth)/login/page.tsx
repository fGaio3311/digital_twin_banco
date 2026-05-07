"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setAuth } from "../../lib/auth";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
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
      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);

      const tokenRes = await fetch(`${BASE}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });

      if (!tokenRes.ok) {
        setError("Usuário ou senha inválidos.");
        return;
      }

      const { access_token } = (await tokenRes.json()) as {
        access_token: string;
      };

      const meRes = await fetch(`${BASE}/user/me`, {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      const me = (await meRes.json()) as {
        username: string;
        role?: string;
        balance?: number;
      };

      const role = me.role ?? "user";
      setAuth(access_token, role, me.username);

      router.push(role === "admin" ? "/admin" : "/dashboard");
    } catch {
      setError("Erro ao conectar ao servidor. Tente novamente.");
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
          <p>Internet Banking</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-banner">{error}</div>}

          <div className="form-field">
            <label htmlFor="u">Usuário</label>
            <input
              id="u"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Seu nome de usuário"
              autoComplete="username"
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
              placeholder="Sua senha"
              autoComplete="current-password"
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? "Entrando..." : "Entrar →"}
          </button>
        </form>

        <p className="login-footer">
          Não tem conta? <Link href="/register">Criar conta</Link>
        </p>
      </div>
    </div>
  );
}
