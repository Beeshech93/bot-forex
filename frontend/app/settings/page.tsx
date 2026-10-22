"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { getConfig, updateConfig } from "@/lib/api";
import type { StrategyConfig } from "@/lib/types";

const fields: Array<[keyof StrategyConfig, string, number, number, number]> = [
  ["ema_fast", "EMA rápida", 2, 200, 1], ["ema_slow", "EMA lenta", 3, 500, 1],
  ["rsi_period", "Período RSI", 2, 100, 1], ["atr_period", "Período ATR", 2, 100, 1],
  ["rsi_buy_min", "Umbral RSI BUY", 50, 100, 0.5], ["rsi_sell_max", "Umbral RSI SELL", 0, 50, 0.5],
  ["min_atr", "ATR mínimo", 0, 10000, 0.00001], ["stop_atr_multiple", "Multiplicador ATR para SL", 0.01, 20, 0.1],
  ["reward_risk_multiple", "Relación riesgo / beneficio", 0.01, 20, 0.1],
];

export default function SettingsPage() {
  const [config, setConfig] = useState<StrategyConfig | null>(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  useEffect(() => { getConfig().then(setConfig).catch((e) => setError(e.message)); }, []);
  async function save() {
    if (!config) return;
    setSaved(false); setError("");
    try { setConfig(await updateConfig(config)); setSaved(true); }
    catch (e) { setError(e instanceof Error ? e.message : "No se pudo guardar la configuración."); }
  }
  return <>
    <PageHeader eyebrow="System / 05" title="Configuración" description="Parámetros validados de la estrategia." />
    <section className="panel">
      <div className="panel-heading"><h2>Estrategia EMA · RSI · ATR</h2><span className="signal-direction">Persistida en base de datos</span></div>
      {error && <p className="error">{error}</p>}
      {config ? <div className="form-grid">
        {fields.map(([key, name, min, max, step]) => <label className="form-field" key={key}>{name}
          <input className="field" type="number" min={min} max={max} step={step} value={config[key] ?? ""}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value === "" ? 0 : Number(e.target.value) })} />
        </label>)}
        <label className="form-field">Spread máximo (puntos; vacío desactiva)
          <input className="field" type="number" min="0" value={config.max_spread_points ?? ""}
            onChange={(e) => setConfig({ ...config, max_spread_points: e.target.value === "" ? null : Number(e.target.value) })} />
        </label>
      </div> : <p className="loading">Cargando parámetros…</p>}
      <div className="toolbar" style={{ marginTop: 18 }}><button className="button" disabled={!config} onClick={save}>Guardar configuración</button>{saved && <span className="status-value">Guardada</span>}</div>
      <p className="footnote" style={{ marginTop: 16 }}>Los valores se validan y guardan en la base de datos del backend.</p>
    </section>
    <section className="panel" style={{ marginTop: 16 }}>
      <div className="panel-heading"><h2>Protección y acceso</h2></div>
      <div className="status-row"><span className="status-name">Autenticación de API</span><span className="status-value">Token Bearer</span></div>
      <div className="status-row"><span className="status-name">Credenciales del backend en navegador</span><span className="status-value">No expuestas</span></div>
      <div className="status-row"><span className="status-name">Ejecución de órdenes</span><span className="status-value">Deshabilitada</span></div>
    </section>
  </>;
}
