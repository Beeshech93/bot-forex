"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { getConfig, runBacktest } from "@/lib/api";
import type { Backtest, StrategyConfig } from "@/lib/types";

const today = new Date().toISOString().slice(0, 10);
const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);

export default function BacktestingPage() {
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState("M5");
  const [startDate, setStartDate] = useState(monthAgo);
  const [endDate, setEndDate] = useState(today);
  const [spread, setSpread] = useState("0");
  const [slippage, setSlippage] = useState("0");
  const [result, setResult] = useState<Backtest | null>(null);
  const [strategy, setStrategy] = useState<StrategyConfig | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => { getConfig().then(setStrategy).catch((e) => setError(e.message)); }, []);
  async function submit() {
    setLoading(true); setError(""); setResult(null);
    try {
      const response = await runBacktest({
        symbol, timeframe,
        start_date: `${startDate}T00:00:00Z`, end_date: `${endDate}T23:59:59Z`,
        spread: Number(spread), slippage: Number(slippage),
        ...(strategy ? { strategy } : {}),
      });
      setResult(response.result);
    } catch (e) { setError(e instanceof Error ? e.message : "No se pudo ejecutar la simulación."); }
    finally { setLoading(false); }
  }
  function downloadCsv() {
    if (!result) return;
    const columns = ["direction", "entry_time", "exit_time", "entry_price", "exit_price", "pnl", "result", "exit_reason"] as const;
    const csv = [columns.join(","), ...result.trades.map((trade) => columns.map((column) => trade[column]).join(","))].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "smart-signals-backtest.csv"; link.click(); URL.revokeObjectURL(url);
  }
  return <>
    <PageHeader eyebrow="Research / 04" title="Backtesting" description="Simulación histórica causal. No envía operaciones al bróker." />
    <section className="panel">
      <div className="panel-heading"><h2>Parámetros de simulación</h2></div>
      <div className="form-grid">
        <label className="form-field">Símbolo<input className="field" value={symbol} onChange={(e) => setSymbol(e.target.value)} /></label>
        <label className="form-field">Temporalidad<select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}><option>M5</option><option>M15</option></select></label>
        <label className="form-field">Desde<input className="field" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} /></label>
        <label className="form-field">Hasta<input className="field" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} /></label>
        <label className="form-field">Spread simulado (unidades de precio)<input className="field" type="number" min="0" step="0.00001" value={spread} onChange={(e) => setSpread(e.target.value)} /></label>
        <label className="form-field">Deslizamiento por lado<input className="field" type="number" min="0" step="0.00001" value={slippage} onChange={(e) => setSlippage(e.target.value)} /></label>
      </div>
      <div className="toolbar" style={{ marginTop: 18 }}><button className="button" disabled={loading || !strategy} onClick={submit}>{loading ? "Ejecutando…" : "Ejecutar backtest"}</button>{result && <button className="button" onClick={downloadCsv}>Descargar CSV</button>}</div>
      {error && <p className="error">{error}</p>}
    </section>
    {result && <section className="panel" style={{ marginTop: 16 }}>
      <div className="panel-heading"><h2>Resultados simulados</h2><span className="muted">{result.trade_count} operaciones</span></div>
      <div className="metric-grid">
        <div className="metric"><span>Porcentaje de aciertos</span><strong>{(result.win_rate * 100).toFixed(1)}%</strong></div>
        <div className="metric"><span>P/L neto</span><strong className={result.net_pnl >= 0 ? "positive" : "negative"}>{result.net_pnl.toFixed(5)}</strong></div>
        <div className="metric"><span>Profit factor</span><strong>{result.profit_factor?.toFixed(2) ?? "—"}</strong></div>
        <div className="metric"><span>Drawdown máximo</span><strong>{result.max_drawdown.toFixed(5)}</strong></div>
      </div>
      <p className="footnote">{result.pnl_units}. Estos resultados no reproducen completamente comisiones, swaps, latencia, gaps ni ejecución real y no predicen resultados futuros.</p>
      <div className="table-wrap"><table><thead><tr><th>Dirección</th><th>Entrada (UTC)</th><th>Salida (UTC)</th><th>Precio entrada</th><th>Precio salida</th><th>P/L</th><th>Motivo salida</th></tr></thead><tbody>{result.trades.map((trade, index) => <tr key={`${trade.entry_time}-${index}`}><td>{trade.direction}</td><td>{trade.entry_time}</td><td>{trade.exit_time}</td><td>{trade.entry_price.toFixed(5)}</td><td>{trade.exit_price.toFixed(5)}</td><td className={trade.pnl >= 0 ? "positive" : "negative"}>{trade.pnl.toFixed(5)}</td><td>{trade.exit_reason}</td></tr>)}</tbody></table></div>
    </section>}
  </>;
}
