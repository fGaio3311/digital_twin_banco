"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import type { ReactNode } from "react";
import { clearAuth } from "../lib/auth";

const NAV = [
  { href: "/admin", label: "Dashboard", icon: "📊" },
  { href: "/admin/simulations", label: "Simulações", icon: "⚡" },
  { href: "/admin/anomalies", label: "Anomalias", icon: "🚨" },
  { href: "/admin/overview", label: "Visão Geral", icon: "🔭" },
  { href: "/admin/metrics", label: "Métricas", icon: "📈" },
  { href: "/admin/summary", label: "Resumo", icon: "📋" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem("dt_token");
    const role = localStorage.getItem("dt_role");
    if (!token) { router.replace("/login"); return; }
    if (role !== "admin") { router.replace("/dashboard"); }
  }, [router]);

  const logout = () => { clearAuth(); router.replace("/login"); };

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-sidebar__logo">
          <h2>🔒 Digital Twin</h2>
          <p>SecOps Bancário</p>
        </div>

        <nav className="admin-sidebar__nav">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={pathname === n.href ? "active" : ""}
            >
              <span>{n.icon}</span>
              <span>{n.label}</span>
            </Link>
          ))}
        </nav>

        <div className="admin-sidebar__footer">
          <Link href="/dashboard">
            <span>🏦</span>
            <span>Voltar ao Banco</span>
          </Link>
          <button
            onClick={logout}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              padding: "9px 12px",
              background: "none",
              border: "none",
              color: "#9aa8c1",
              cursor: "pointer",
              fontSize: "0.84rem",
              width: "100%",
              borderRadius: 8,
              transition: "color 0.14s",
            }}
          >
            <span>↩</span>
            <span>Sair</span>
          </button>
        </div>
      </aside>

      <main className="admin-main">{children}</main>
    </div>
  );
}
