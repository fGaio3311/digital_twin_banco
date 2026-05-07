import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'Digital Twin SecOps Bancário',
  description: 'Painel moderno para monitoramento de risco e conformidade.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
