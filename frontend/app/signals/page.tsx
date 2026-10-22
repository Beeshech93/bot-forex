"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { getSignal, getSignalHistory, getSymbols } from "@/lib/api";
import type { Signal, SymbolItem } from "@/lib/types";

export default function SignalsPage() {
  const [symbols, setSymbols] = useState<SymbolItem[]>([]);
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState("M5");
  const [signal, setSignal] = useState<Signal | null>(null);
  const [history, setHistory] = useState<Signal[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { getSymbols().then((data) => { setSymbols(data.items); if (data.items[0]) setSymbol(data.items.find((item) => item.name.includes("EURUSD"))?.name || data.items[0].name); }).catch(() => undefined); }, []);
  useEffect(() => {
    getSignal(symbol, timeframe).then((value) => { setSignal(value); return getSignalHistory(); })
      .then((data) => setHistory(data.items)).catch((e) => { setSignal(null); setError(e.message); });
  }, [symbol, timeframe]);
  return <>
    <PageHeader eyebrow="Signals / 03" title="Señales" description="Lecturas técnicas sobre velas cerradas. Cada resultado es informativo." />
    <section className="panel">
      <div className="panel-heading"><h2>Análisis actual</h2><div className="toolbar">
        <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)} aria-label="Símbolo">{(symbols.length ? symbols : [{ name: "EURUSD", description: "", visible: true }]).map((item) => <option key={item.name}>{item.name}</option>)}</select>
        <select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)} aria-label="Temporalidad"><option>M5</option><option>M15</option></select>
      </div></div>
      {error && <div className="error">{error}</div>}
      {signal ? <>
        <div className="list-row"><span className="symbol-line"><span className={`signal-direction ${signal.direction}`}>{signal.direction}</span><b className="mono">{signal.symbol}</b></span><span className="muted">{signal.timeframe} · {signal.data_valid ? "Datos válidos" : "Datos incompletos"}</span></div>
        <div className="metric-grid">
          <div className="metric"><span>Precio referencia</span><strong>{signal.reference_price?.toFixed(5) ?? "—"}</strong></div>
          <div className="metric"><span>Stop Loss teórico</span><strong>{signal.stop_loss?.toFixed(5) ?? "—"}</strong></div>
          <div className="metric"><span>Take Profit teórico</span><strong>{signal.take_profit?.toFixed(5) ?? "—"}</strong></div>
          <div className="metric"><span>Riesgo / beneficio</span><strong>{signal.reward_risk ? `${signal.reward_risk}:1` : "—"}</strong></div>
        </div>
        <h3 style={{ fontSize: 12, fontWeight: 500 }}>Justificación técnica</h3>
        {signal.reasons.map((reason) => <div className="status-row" key={reason}><span className="status-name">{reason}</span></div>)}
        <p className="footnote">Última vela cerrada: {signal.last_closed_candle_time || "—"} (UTC). Generación: {signal.generated_at || "—"}</p>
      </> : <div className="empty-state"><div><strong>Consultando señal…</strong>Si MT5 no está conectado, la API devolverá NO SIGNAL.</div></div>}
      <div className="notice" style={{ marginTop: 16 }}><strong>Solo referencia analítica</strong>Los niveles calculados no son órdenes y no garantizan resultados.</div>
    </section>
    <section className="panel" style={{ marginTop: 16 }}>
      <div className="panel-heading"><h2>Historial de señales</h2><span className="muted">{history.length} registros</span></div>
      {history.length ? <div className="table-wrap"><table><thead><tr><th>Dirección</th><th>Símbolo</th><th>Temporalidad</th><th>Precio referencia</th><th>Vela cerrada (UTC)</th></tr></thead><tbody>{history.map((item, index) => <tr key={`${item.symbol}-${item.last_closed_candle_time}-${index}`}><td><span className={`signal-direction ${item.direction}`}>{item.direction}</span></td><td>{item.symbol}</td><td>{item.timeframe}</td><td>{item.reference_price?.toFixed(5) ?? "—"}</td><td>{item.last_closed_candle_time || "—"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><div><strong>Sin historial todavía</strong>Las lecturas válidas se guardarán al consultarlas.</div></div>}
    </section>
  </>;
}
