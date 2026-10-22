"""Causal OHLC backtest engine with conservative intrabar exit handling."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.services.market_service import InsufficientMarketDataError, calculate_indicators
from app.strategies.ema_rsi_atr import StrategyConfig


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$")
    timeframe: Literal["M5", "M15"]
    start_date: datetime
    end_date: datetime
    spread: float = Field(default=0.0, ge=0.0, le=10_000.0, description="Simulated spread in quote-price units")
    slippage: float = Field(default=0.0, ge=0.0, le=10_000.0, description="Per-side slippage in quote-price units")
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)

    def validate_range(self) -> "BacktestRequest":
        if self.start_date.tzinfo is None or self.end_date.tzinfo is None:
            raise ValueError("start_date and end_date must include a timezone")
        if self.start_date >= self.end_date:
            raise ValueError("start_date must precede end_date")
        self.strategy.validate_periods()
        return self


class SimulatedTrade(BaseModel):
    direction: Literal["BUY", "SELL"]
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    result: Literal["win", "loss", "breakeven"]
    exit_reason: Literal["stop_loss", "take_profit", "end_of_data"]


class BacktestResult(BaseModel):
    symbol: str
    timeframe: Literal["M5", "M15"]
    start_date: datetime
    end_date: datetime
    data_points: int
    trades: list[SimulatedTrade]
    trade_count: int
    win_rate: float
    net_pnl: float
    profit_factor: float | None
    max_drawdown: float
    expectancy: float
    average_realized_reward_risk: float | None
    pnl_units: str = "quote-price units for a one-unit position"
    assumptions: list[str]


def run_backtest(candles: list[dict], request: BacktestRequest) -> BacktestResult:
    request.validate_range()
    minimum = max(request.strategy.ema_slow, request.strategy.rsi_period + 1, request.strategy.atr_period + 1)
    if len(candles) < minimum + 2:
        raise InsufficientMarketDataError(f"At least {minimum + 2} candles are required for a backtest")
    frame = calculate_indicators(candles, request.strategy.ema_fast, request.strategy.ema_slow,
                                 request.strategy.rsi_period, request.strategy.atr_period)
    trades: list[SimulatedTrade] = []
    next_available = minimum
    index = minimum
    while index < len(frame) - 1:
        current, previous = frame.iloc[index], frame.iloc[index - 1]
        needed = (current["ema_fast"], current["ema_slow"], current["rsi"], current["atr"])
        if any(value != value for value in needed):
            index += 1
            continue
        direction = None
        crossed_up = previous["close"] <= previous["ema_fast"] and current["close"] > current["ema_fast"]
        crossed_down = previous["close"] >= previous["ema_fast"] and current["close"] < current["ema_fast"]
        spread_points = current.get("spread")
        spread_ok = (request.strategy.max_spread_points is None or
                     (spread_points is not None and int(spread_points) <= request.strategy.max_spread_points))
        if spread_ok and current["atr"] >= request.strategy.min_atr:
            if current["ema_fast"] > current["ema_slow"] and crossed_up and current["rsi"] >= request.strategy.rsi_buy_min:
                direction = "BUY"
            elif current["ema_fast"] < current["ema_slow"] and crossed_down and current["rsi"] <= request.strategy.rsi_sell_max:
                direction = "SELL"
        entry_index = index + 1
        if direction is None or entry_index < next_available:
            index += 1
            continue
        entry_bar = frame.iloc[entry_index]
        half_spread = request.spread / 2
        entry_price = float(entry_bar["open"] + half_spread + request.slippage
                            if direction == "BUY" else entry_bar["open"] - half_spread - request.slippage)
        risk = float(current["atr"] * request.strategy.stop_atr_multiple)
        stop = entry_price - risk if direction == "BUY" else entry_price + risk
        target_distance = risk * request.strategy.reward_risk_multiple
        target = entry_price + target_distance if direction == "BUY" else entry_price - target_distance
        exit_index = len(frame) - 1
        exit_reason: Literal["stop_loss", "take_profit", "end_of_data"] = "end_of_data"
        raw_exit = float(frame.iloc[-1]["close"])
        for scan in range(entry_index, len(frame)):
            bar = frame.iloc[scan]
            if direction == "BUY":
                stop_hit, target_hit = bar["low"] <= stop, bar["high"] >= target
            else:
                stop_hit, target_hit = bar["high"] >= stop, bar["low"] <= target
            if stop_hit:  # If both thresholds appear in one candle, assume the stop was first.
                exit_index, exit_reason = scan, "stop_loss"
                raw_exit = stop
                break
            if target_hit:
                exit_index, exit_reason = scan, "take_profit"
                raw_exit = target
                break
        exit_price = float(raw_exit - half_spread - request.slippage
                           if direction == "BUY" else raw_exit + half_spread + request.slippage)
        pnl = exit_price - entry_price if direction == "BUY" else entry_price - exit_price
        result = "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven"
        trades.append(SimulatedTrade(
            direction=direction, entry_time=entry_bar["time"], exit_time=frame.iloc[exit_index]["time"],
            entry_price=entry_price, exit_price=exit_price, stop_loss=stop, take_profit=target,
            pnl=pnl, result=result, exit_reason=exit_reason,
        ))
        next_available = exit_index + 1
        index = next_available
    return _metrics(trades, request, len(candles))


def _metrics(trades: list[SimulatedTrade], request: BacktestRequest, data_points: int) -> BacktestResult:
    pnls = [trade.pnl for trade in trades]
    gains = sum(value for value in pnls if value > 0)
    losses = -sum(value for value in pnls if value < 0)
    equity = peak = drawdown = 0.0
    for value in pnls:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    realized_rr = [abs(trade.pnl / abs(trade.entry_price - trade.stop_loss))
                   for trade in trades if trade.entry_price != trade.stop_loss]
    return BacktestResult(
        symbol=request.symbol, timeframe=request.timeframe, start_date=request.start_date,
        end_date=request.end_date, data_points=data_points, trades=trades, trade_count=len(trades),
        win_rate=(sum(1 for value in pnls if value > 0) / len(trades) if trades else 0.0),
        net_pnl=sum(pnls), profit_factor=(gains / losses if losses else None),
        max_drawdown=drawdown, expectancy=(sum(pnls) / len(trades) if trades else 0.0),
        average_realized_reward_risk=(sum(realized_rr) / len(realized_rr) if realized_rr else None),
        assumptions=[
            "Entry is simulated at the next candle open after the signal candle.",
            "Stop loss is checked before take profit when both occur within one OHLC candle.",
            "Spread and slippage use the supplied quote-price-unit assumptions.",
            "One-unit positions are used; commission, swaps, latency, gaps, and execution behavior are not modeled.",
        ],
    )
