import type { Metadata } from "next";
import { AuthGate } from "@/components/auth-gate";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Signals FX",
  description: "Plataforma de análisis y señales de Forex en modo de solo lectura.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body><AuthGate><AppShell>{children}</AppShell></AuthGate></body>
    </html>
  );
}
