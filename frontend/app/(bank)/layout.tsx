"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import type { ReactNode } from "react";
import { clearAuth, getUsername } from "../lib/auth";

export default function BankLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [username, setUsername] = useState("");
  const [showAdmin, setShowAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("dt_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    setUsername(getUsername());
    setShowAdmin(localStorage.getItem("dt_role") === "admin");
  }, [router]);

  const handleLogout = () => {
    clearAuth();
    router.replace("/login");
  };

  const links = [
    { href: "/dashboard", label: "Início" },
    { href: "/statement", label: "Extrato" },
    { href: "/transfer", label: "Transferir" },
  ];

  return (
    <div
      style={{ minHeight: "100vh", background: "#f0f4f8", color: "#111827" }}
    >
      <nav className="bank-nav">
        <div className="bank-nav__logo">🏦 BancoTwin</div>
        <div className="bank-nav__links">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={pathname === l.href ? "active" : ""}
            >
              {l.label}
            </Link>
          ))}
        </div>
        <div className="bank-nav__user">
          {showAdmin && (
            <Link
              href="/admin"
              style={{
                background: "rgba(104,224,255,0.18)",
                color: "#68e0ff",
                padding: "4px 12px",
                borderRadius: 999,
                fontSize: "0.75rem",
                fontWeight: 700,
                border: "1px solid rgba(104,224,255,0.35)",
                marginRight: 8,
                textDecoration: "none",
              }}
            >
              ⚡ Twin
            </Link>
          )}
          <span style={{ fontSize: "0.9rem" }}>{username}</span>
          <button onClick={handleLogout}>Sair</button>
        </div>
      </nav>
      {children}
    </div>
  );
}
