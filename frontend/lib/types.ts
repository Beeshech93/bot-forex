export type Health = { status: string; service: string };
export type TerminalStatus = {
  status: "connected" | "disconnected";
  available: boolean;
  platform_supported: boolean;
  message: string;
};
export type SymbolItem = { name: string; description: string; visible: boolean };
export type Candle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  spread?: number;
};
export type IndicatorPoint = { time: string; ema_fast: number | null; ema_slow: number | null };
export type IndicatorResponse = {
  values: { ema_fast: number | null; ema_slow: number | null; rsi: number | null; atr: number | null };
  series: IndicatorPoint[];
};
export type Signal = {
  direction: "BUY" | "SELL" | "NO_SIGNAL";
  symbol: string;
  timeframe: "M5" | "M15";
  reference_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  stop_distance?: number | null;
  reward_risk?: number | null;
  generated_at: string | null;
  last_closed_candle_time: string | null;
  data_valid: boolean;
  reasons: string[];
  indicators: Record<string, number | null>;
};
export type Backtest = {
  trade_count: number;
  win_rate: number;
  net_pnl: number;
  profit_factor: number | null;
  max_drawdown: number;
  expectancy: number;
  average_realized_reward_risk: number | null;
  pnl_units: string;
  trades: Array<{
    direction: "BUY" | "SELL";
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    pnl: number;
    result: string;
    exit_reason: string;
  }>;
  assumptions: string[];
};
export type StrategyConfig = {
  ema_fast: number;
  ema_slow: number;
  rsi_period: number;
  atr_period: number;
  rsi_buy_min: number;
  rsi_sell_max: number;
  min_atr: number;
  max_spread_points: number | null;
  stop_atr_multiple: number;
  reward_risk_multiple: number;
};
