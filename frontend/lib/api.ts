import type { Backtest, Candle, Health, IndicatorResponse, Signal, StrategyConfig, SymbolItem, TerminalStatus } from "@/lib/types";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/proxy/${path}`, { ...init, cache: "no-store" });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : data.detail?.message;
    throw new Error(detail || `API request failed (${response.status})`);
  }
  return data as T;
}

export const getHealth = () => api<Health>("health");
export const getTerminal = () => api<TerminalStatus>("api/v1/terminal");
export const getSymbols = () => api<{ items: SymbolItem[]; count: number }>("api/v1/symbols");
export const getCandles = (symbol: string, timeframe: string, limit = 200) =>
  api<{ items: Candle[]; count: number; timezone: string }>(
    `api/v1/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=${limit}`,
  );
export const getIndicators = (symbol: string, timeframe: string) =>
  api<IndicatorResponse>(
    `api/v1/indicators?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`,
  );
export const getSignal = (symbol: string, timeframe: string) =>
  api<Signal>(`api/v1/signals?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`);
export const runBacktest = (body: unknown) =>
  api<{ id: string; status: string; result: Backtest }>("api/v1/backtest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
export const getConfig = () => api<StrategyConfig>("api/v1/config");
export const updateConfig = (config: StrategyConfig) =>
  api<StrategyConfig>("api/v1/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
export const getSignalHistory = (limit = 25) =>
  api<{ count: number; items: Signal[] }>(`api/v1/signals/history?limit=${limit}`);
