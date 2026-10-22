"use client";

import { useEffect, useState } from "react";
import { CandleChart } from "@/components/candle-chart";
import { PageHeader } from "@/components/page-header";
import { getCandles, getIndicators, getSymbols } from "@/lib/api";
import type { Candle, IndicatorPoint, IndicatorResponse, SymbolItem } from "@/lib/types";

export default function MarketPage() {
  const [symbols, setSymbols] = useState<SymbolItem[]>([]);
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState("M5");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [indicators, setIndicators] = useState<IndicatorPoint[]>([]);
  const [indicatorValues, setIndicatorValues] = useState<IndicatorResponse["values"] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => { getSymbols().then((data) => { setSymbols(data.items); if (data.items[0]) setSymbol(data.items.find((item) => item.name.includes("EURUSD"))?.name || data.items[0].name); }).catch(() => undefined); }, []);
  useEffect(() => {
    if (!symbol) return;
    setLoading(true); setError("");
    Promise.all([getCandles(symbol, timeframe), getIndicators(symbol, timeframe)])
      .then(([c, i]) => { setCandles(c.items); setIndicators(i.series); setIndicatorValues(i.values); })
      .catch((e) => { setCandles([]); setIndicators([]); setIndicatorValues(null); setError(e.message); })
      .finally(() => setLoading(false));
  }, [symbol, timeframe]);
  const latest = indicators[indicators.length - 1];
  return <>
    <PageHeader eyebrow="Market / 02" title="Mercado" description="Velas cerradas e indicadores técnicos del terminal conectado." />
    <section className="panel">
      <div className="panel-heading"><h2>Precio y tendencia</h2><div className="toolbar">
        <select className="select" value={symbol} onChange={(e) => setSymbol(e.target.value)} aria-label="Símbolo">
          {(symbols.length ? symbols : [{ name: "EURUSD", description: "", visible: true }]).map((item) => <option key={item.name} value={item.name}>{item.name}</option>)}
        </select>
        <select className="select" value={timeframe} onChange={(e) => setTimeframe(e.target.value)} aria-label="Temporalidad"><option>M5</option><option>M15</option></select>
      </div></div>
      {loading ? <div className="loading">Cargando datos cerrados…</div> : error ? <div className="empty-state"><div><strong>Datos no disponibles</strong>{error}</div></div> : candles.length ? <CandleChart candles={candles} indicators={indicators} /> : <div className="empty-state"><div><strong>Sin velas para mostrar</strong>Conecta el terminal MetaTrader 5 para consultar precios.</div></div>}
      <div className="metric-grid">
        <div className="metric"><span>EMA 20</span><strong>{latest?.ema_fast?.toFixed(5) ?? "—"}</strong></div>
        <div className="metric"><span>EMA 50</span><strong>{latest?.ema_slow?.toFixed(5) ?? "—"}</strong></div>
        <div className="metric"><span>RSI 14</span><strong>{indicatorValues?.rsi?.toFixed(2) ?? "—"}</strong></div>
        <div className="metric"><span>ATR 14</span><strong>{indicatorValues?.atr?.toFixed(5) ?? "—"}</strong></div>
      </div>
      <p className="footnote">Los timestamps de los datos se expresan en UTC. La API omite la vela que aún se está formando.</p>
    </section>
  </>;
}
