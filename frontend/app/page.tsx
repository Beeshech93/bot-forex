"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { getHealth, getSignal, getSymbols, getTerminal } from "@/lib/api";
import type { Health, Signal, SymbolItem, TerminalStatus } from "@/lib/types";

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null);
  const [terminal, setTerminal] = useState<TerminalStatus | null>(null);
  const [symbols, setSymbols] = useState<SymbolItem[]>([]);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
    getTerminal().then(setTerminal).catch(() => setTerminal(null));
    getSymbols().then((data) => {
      setSymbols(data.items);
      const first = data.items.find((item) => item.name.toUpperCase().includes("EURUSD")) || data.items[0];
      if (first) getSignal(first.name, "M5").then(setSignal).catch((e) => setError(e.message));
    }).catch((e) => setError(e.message));
  }, []);
  return <>
    <PageHeader eyebrow="Overview / 01" title="Dashboard" description="Resumen de mercado y actividad del sistema." />
    <section className="grid stats-grid">
      <article className="panel stat-card"><div className="stat-title">Estado del backend</div><div className="stat-number" style={{ color: health ? "var(--green)" : "#d79b6c" }}>{health?.status === "ok" ? "Online" : "—"}</div><div className="stat-foot">API FastAPI</div></article>
      <article className="panel stat-card"><div className="stat-title">Terminal MetaTrader 5</div><div className="stat-number" style={{ color: terminal?.status === "connected" ? "var(--green)" : "#d79b6c" }}>{terminal?.status === "connected" ? "Conectado" : "Desconectado"}</div><div className="stat-foot">{terminal?.message || "Esperando estado del terminal"}</div></article>
      <article className="panel stat-card"><div className="stat-title">Símbolos disponibles</div><div className="stat-number">{symbols.length || "—"}</div><div className="stat-foot">Reportados por el bróker</div></article>
      <article className="panel stat-card"><div className="stat-title">Última señal analizada</div><div className="stat-number"><span className={`signal-direction ${signal?.direction || ""}`}>{signal?.direction || "—"}</span></div><div className="stat-foot">{signal?.symbol || "Sin datos"} · {signal?.timeframe || "M5"}</div></article>
    </section>
    <section className="grid content-grid">
      <article className="panel">
        <div className="panel-heading"><h2>Señal más reciente</h2><Link href="/signals">Ver análisis →</Link></div>
        {error && <p className="error">{error}</p>}
        {signal ? <>
          <div className="list-row"><span className="symbol-line"><span className={`signal-direction ${signal.direction}`}>{signal.direction}</span><b className="mono">{signal.symbol}</b></span><span className="muted">{signal.timeframe}</span></div>
          <div className="metric-grid">
            <div className="metric"><span>Precio referencia</span><strong>{signal.reference_price?.toFixed(5) ?? "—"}</strong></div>
            <div className="metric"><span>Stop Loss teórico</span><strong>{signal.stop_loss?.toFixed(5) ?? "—"}</strong></div>
            <div className="metric"><span>Take Profit teórico</span><strong>{signal.take_profit?.toFixed(5) ?? "—"}</strong></div>
            <div className="metric"><span>Riesgo / beneficio</span><strong>{signal.reward_risk ? `${signal.reward_risk.toFixed(1)} : 1` : "—"}</strong></div>
          </div>
          <p className="footnote">{signal.reasons.join(" · ")}</p>
        </> : <div className="empty-state"><div><strong>Esperando conexión al terminal</strong>Al conectar MT5 en Windows, el dashboard mostrará los datos.</div></div>}
      </article>
      <article className="panel">
        <div className="panel-heading"><h2>Conexiones</h2></div>
        <div className="status-row"><span className="status-name"><span className="dot" /> API del servicio</span><span className={`status-value ${health ? "" : "offline"}`}>{health ? "Activa" : "No disponible"}</span></div>
        <div className="status-row"><span className="status-name"><span className="dot" style={{ background: terminal?.status === "connected" ? "#80cf8f" : "#d89b67" }} /> Terminal MT5</span><span className={`status-value ${terminal?.status === "connected" ? "" : "offline"}`}>{terminal?.status === "connected" ? "Conectado" : "Desconectado"}</span></div>
        <div className="notice" style={{ marginTop: 20 }}><strong>Solo análisis</strong>Smart Signals FX nunca abre, modifica ni cierra posiciones. Los niveles mostrados son referencias analíticas.</div>
      </article>
    </section>
  </>;
}
