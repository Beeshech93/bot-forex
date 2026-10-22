"""Market data validation and technical indicator calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.mt5_service import MT5Service, mt5_service


class InsufficientMarketDataError(ValueError):
    """Raised when historical data cannot safely support a calculation."""


def calculate_indicators(candles: list[dict], ema_fast: int = 20, ema_slow: int = 50,
                         rsi_period: int = 14, atr_period: int = 14) -> pd.DataFrame:
    """Return a copy of OHLC candles with EMA, Wilder RSI, and Wilder ATR columns."""
    minimum = max(ema_fast, ema_slow, rsi_period + 1, atr_period + 1)
    if min(ema_fast, ema_slow, rsi_period, atr_period) < 2 or ema_fast >= ema_slow:
        raise ValueError("Indicator periods are invalid")
    if len(candles) < minimum:
        raise InsufficientMarketDataError(f"At least {minimum} closed candles are required")
    frame = pd.DataFrame(candles).copy()
    required_columns = {"time", "open", "high", "low", "close"}
    if not required_columns.issubset(frame.columns):
        raise InsufficientMarketDataError("Candle data is incomplete")
    if frame[list(required_columns - {"time"})].isnull().any().any():
        raise InsufficientMarketDataError("Candle data contains missing prices")
    close = pd.to_numeric(frame["close"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    if not np.isfinite(close.to_numpy()).all() or not np.isfinite(high.to_numpy()).all() or not np.isfinite(low.to_numpy()).all():
        raise InsufficientMarketDataError("Candle data contains invalid prices")
    frame["ema_fast"] = close.ewm(span=ema_fast, adjust=False, min_periods=ema_fast).mean()
    frame["ema_slow"] = close.ewm(span=ema_slow, adjust=False, min_periods=ema_slow).mean()
    delta = close.diff()
    average_gain = delta.clip(lower=0).ewm(alpha=1 / rsi_period, adjust=False, min_periods=rsi_period).mean()
    average_loss = (-delta.clip(upper=0)).ewm(alpha=1 / rsi_period, adjust=False, min_periods=rsi_period).mean()
    ratio = average_gain / average_loss.replace(0, np.nan)
    frame["rsi"] = 100 - (100 / (1 + ratio))
    frame.loc[(average_loss == 0) & (average_gain > 0), "rsi"] = 100.0
    frame.loc[(average_gain == 0) & (average_loss > 0), "rsi"] = 0.0
    frame.loc[(average_gain == 0) & (average_loss == 0), "rsi"] = 50.0
    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()], axis=1
    ).max(axis=1)
    frame["atr"] = true_range.ewm(alpha=1 / atr_period, adjust=False, min_periods=atr_period).mean()
    return frame


class MarketService:
    def __init__(self, terminal: MT5Service = mt5_service) -> None:
        self.terminal = terminal

    def get_closed_candles(self, symbol: str, timeframe: str, limit: int) -> list[dict]:
        if timeframe not in {"M5", "M15"}:
            raise ValueError("Timeframe must be M5 or M15")
        candles = self.terminal.candles(symbol, timeframe, limit)
        if not candles:
            raise InsufficientMarketDataError("No closed candles are available for this symbol")
        times = [item["time"] for item in candles]
        if times != sorted(times) or len(times) != len(set(times)):
            raise InsufficientMarketDataError("Candle times are duplicated or out of order")
        return candles


market_service = MarketService()
