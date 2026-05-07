import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "BancoTwin",
  description: "Internet Banking & Digital Twin SecOps.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
