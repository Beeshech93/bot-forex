"""EMA/RSI/ATR signal generation; returns analysis only and never places orders."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from app.services.market_service import calculate_indicators

SignalDirection = Literal["BUY", "SELL", "NO_SIGNAL"]


class StrategyConfig(BaseModel):
    ema_fast: int = Field(default=20, ge=2, le=200)
    ema_slow: int = Field(default=50, ge=3, le=500)
    rsi_period: int = Field(default=14, ge=2, le=100)
    atr_period: int = Field(default=14, ge=2, le=100)
    rsi_buy_min: float = Field(default=55.0, ge=50.0, le=100.0)
    rsi_sell_max: float = Field(default=45.0, ge=0.0, le=50.0)
    min_atr: float = Field(default=0.0, ge=0.0)
    max_spread_points: int | None = Field(default=None, ge=0)
    stop_atr_multiple: float = Field(default=1.5, gt=0.0, le=20.0)
    reward_risk_multiple: float = Field(default=2.0, gt=0.0, le=20.0)

    def validate_periods(self) -> "StrategyConfig":
        if self.ema_fast >= self.ema_slow:
            raise ValueError("ema_fast must be lower than ema_slow")
        if self.rsi_sell_max >= self.rsi_buy_min:
            raise ValueError("RSI sell threshold must be below the buy threshold")
        return self


class SignalResult(BaseModel):
    direction: SignalDirection
    symbol: str
    timeframe: Literal["M5", "M15"]
    reference_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    stop_distance: float | None = None
    reward_risk: float | None = None
    generated_at: datetime
    last_closed_candle_time: datetime | None = None
    data_valid: bool
    reasons: list[str]
    indicators: dict[str, float | None]


def generate_signal(symbol: str, timeframe: Literal["M5", "M15"], candles: list[dict],
                    config: StrategyConfig | None = None) -> SignalResult:
    config = (config or StrategyConfig()).validate_periods()
    now = datetime.now(timezone.utc)
    empty_indicators = {"ema_fast": None, "ema_slow": None, "rsi": None, "atr": None}
    try:
        frame = calculate_indicators(candles, config.ema_fast, config.ema_slow,
                                     config.rsi_period, config.atr_period)
    except (ValueError, KeyError) as exc:
        return SignalResult(
            direction="NO_SIGNAL", symbol=symbol, timeframe=timeframe,
            generated_at=now, last_closed_candle_time=candles[-1].get("time") if candles else None,
            data_valid=False, reasons=[f"Market data is not sufficient: {exc}"], indicators=empty_indicators,
        )
    current = frame.iloc[-1]
    previous = frame.iloc[-2]
    last_time = current["time"]
    values = {key: float(current[key]) if current[key] == current[key] else None
              for key in ("ema_fast", "ema_slow", "rsi", "atr")}
    if any(value is None for value in values.values()):
        return SignalResult(direction="NO_SIGNAL", symbol=symbol, timeframe=timeframe,
                            generated_at=now, last_closed_candle_time=last_time,
                            data_valid=False, reasons=["Required indicators are unavailable"], indicators=values)
    if config.max_spread_points is not None:
        spread = current.get("spread")
        if spread is None:
            return SignalResult(direction="NO_SIGNAL", symbol=symbol, timeframe=timeframe,
                                generated_at=now, last_closed_candle_time=last_time,
                                data_valid=False, reasons=["Spread filter is enabled but spread data is missing"],
                                indicators=values)
        if int(spread) > config.max_spread_points:
            return SignalResult(direction="NO_SIGNAL", symbol=symbol, timeframe=timeframe,
                                generated_at=now, last_closed_candle_time=last_time,
                                data_valid=True, reasons=["Spread exceeds configured maximum"], indicators=values)
    if values["atr"] < config.min_atr:
        return SignalResult(direction="NO_SIGNAL", symbol=symbol, timeframe=timeframe,
                            generated_at=now, last_closed_candle_time=last_time,
                            data_valid=True, reasons=["ATR is below configured minimum"], indicators=values)
    crossed_up = previous["close"] <= previous["ema_fast"] and current["close"] > current["ema_fast"]
    crossed_down = previous["close"] >= previous["ema_fast"] and current["close"] < current["ema_fast"]
    direction: SignalDirection = "NO_SIGNAL"
    reasons: list[str] = []
    if current["ema_fast"] > current["ema_slow"] and crossed_up and current["rsi"] >= config.rsi_buy_min:
        direction = "BUY"
        reasons = ["EMA fast is above EMA slow", "Closed candle crossed above EMA fast",
                   f"RSI {current['rsi']:.2f} meets buy threshold {config.rsi_buy_min:.2f}",
                   f"ATR {current['atr']:.6f} meets minimum {config.min_atr:.6f}"]
    elif current["ema_fast"] < current["ema_slow"] and crossed_down and current["rsi"] <= config.rsi_sell_max:
        direction = "SELL"
        reasons = ["EMA fast is below EMA slow", "Closed candle crossed below EMA fast",
                   f"RSI {current['rsi']:.2f} meets sell threshold {config.rsi_sell_max:.2f}",
                   f"ATR {current['atr']:.6f} meets minimum {config.min_atr:.6f}"]
    else:
        reasons = ["Configured trend, closed-candle crossing, RSI, and volatility conditions did not all match"]
    if direction == "NO_SIGNAL":
        return SignalResult(direction=direction, symbol=symbol, timeframe=timeframe,
                            generated_at=now, last_closed_candle_time=last_time,
                            data_valid=True, reasons=reasons, indicators=values)
    reference = float(current["close"])
    stop_distance = float(current["atr"]) * config.stop_atr_multiple
    if direction == "BUY":
        stop, target = reference - stop_distance, reference + stop_distance * config.reward_risk_multiple
    else:
        stop, target = reference + stop_distance, reference - stop_distance * config.reward_risk_multiple
    return SignalResult(
        direction=direction, symbol=symbol, timeframe=timeframe, reference_price=reference,
        stop_loss=stop, take_profit=target, stop_distance=stop_distance,
        reward_risk=config.reward_risk_multiple, generated_at=now,
        last_closed_candle_time=last_time, data_valid=True, reasons=reasons, indicators=values,
    )
