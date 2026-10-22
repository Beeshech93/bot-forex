"""Read-only MetaTrader 5 terminal adapter.

This adapter intentionally exposes no order, trade, or account-mutation methods.
It never calls ``login``; the terminal must already be connected by its operator.
"""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

try:  # MetaTrader5 is distributed for Windows; keep API importable elsewhere.
    import MetaTrader5 as _mt5
except ImportError:  # pragma: no cover - behavior is covered with adapter mocks
    _mt5 = None


@dataclass(frozen=True)
class TerminalStatus:
    connected: bool
    available: bool
    platform_supported: bool
    message: str


class MT5Service:
    """Small synchronous adapter around the read-only MT5 query surface."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client if client is not None else _mt5
        self._initialized_here = False

    def status(self) -> TerminalStatus:
        if platform.system() != "Windows":
            return TerminalStatus(False, self._client is not None, False, "MetaTrader 5 requires Windows")
        if self._client is None:
            return TerminalStatus(False, False, True, "MetaTrader5 package is not installed")
        if not self._ensure_initialized():
            return TerminalStatus(False, True, True, "Unable to initialize MetaTrader 5 terminal")
        terminal = self._client.terminal_info()
        account = self._client.account_info()
        connected = bool(terminal and account and getattr(terminal, "connected", False))
        return TerminalStatus(
            connected,
            True,
            True,
            "Connected" if connected else "Terminal is not connected to a broker",
        )

    def symbols(self) -> list[dict[str, Any]]:
        status = self.status()
        if not status.connected:
            raise MT5UnavailableError(status.message)
        raw_symbols = self._client.symbols_get()
        if raw_symbols is None:
            error = self._client.last_error()
            logger.warning("MT5 symbols query failed", extra={"mt5_error_code": error[0] if error else None})
            raise MT5UnavailableError("Unable to retrieve symbols from MetaTrader 5")
        return [
            {
                "name": str(item.name),
                "description": str(getattr(item, "description", "")),
                "visible": bool(getattr(item, "visible", False)),
            }
            for item in raw_symbols
        ]

    def candles(self, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]]:
        """Fetch the most recent closed bars; MT5 position zero is still forming."""
        status = self.status()
        if not status.connected:
            raise MT5UnavailableError(status.message)
        mt5_timeframe = self._timeframe_constant(timeframe)
        if mt5_timeframe is None:
            raise MT5UnavailableError(f"Timeframe {timeframe} is unavailable")
        rates = self._client.copy_rates_from_pos(symbol, mt5_timeframe, 1, limit)
        if rates is None:
            error = self._client.last_error()
            logger.warning("MT5 candles query failed", extra={"mt5_error_code": error[0] if error else None})
            raise MT5UnavailableError("Unable to retrieve closed candles from MetaTrader 5")
        return self._normalize_rates(rates)

    def candles_between(self, symbol: str, timeframe: str, start: datetime, end: datetime,
                        max_bars: int) -> list[dict[str, Any]]:
        status = self.status()
        if not status.connected:
            raise MT5UnavailableError(status.message)
        mt5_timeframe = self._timeframe_constant(timeframe)
        if mt5_timeframe is None:
            raise MT5UnavailableError(f"Timeframe {timeframe} is unavailable")
        rates = self._client.copy_rates_range(symbol, mt5_timeframe, start, end)
        if rates is None:
            error = self._client.last_error()
            logger.warning("MT5 historical query failed", extra={"mt5_error_code": error[0] if error else None})
            raise MT5UnavailableError("Unable to retrieve historical candles from MetaTrader 5")
        if len(rates) > max_bars:
            raise MT5UnavailableError(f"Requested range has more than the {max_bars} bar limit")
        normalized = self._normalize_rates(rates)
        now = datetime.now(timezone.utc)
        duration_seconds = 5 * 60 if timeframe == "M5" else 15 * 60
        return [row for row in normalized if row["time"].timestamp() + duration_seconds <= now.timestamp()]

    def _timeframe_constant(self, timeframe: str) -> Any:
        return getattr(self._client, f"TIMEFRAME_{timeframe}", None)

    @staticmethod
    def _normalize_rates(rates: Any) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for row in rates:
            timestamp = int(row["time"])
            output.append({
                "time": datetime.fromtimestamp(timestamp, tz=timezone.utc),
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "tick_volume": int(row["tick_volume"]), "spread": int(row["spread"]),
                "real_volume": int(row["real_volume"]),
            })
        return output

    def close(self) -> None:
        """Release only a terminal session initialized by this process."""
        if self._client is not None and self._initialized_here:
            self._client.shutdown()
            self._initialized_here = False

    def _ensure_initialized(self) -> bool:
        terminal = self._client.terminal_info()
        if terminal is not None:
            return True
        settings = get_settings()
        kwargs = {"path": settings.mt5_terminal_path} if settings.mt5_terminal_path else {}
        initialized = bool(self._client.initialize(**kwargs))
        self._initialized_here = initialized
        if not initialized:
            error = self._client.last_error()
            logger.warning("MT5 initialization failed", extra={"mt5_error_code": error[0] if error else None})
        return initialized


class MT5UnavailableError(RuntimeError):
    """Raised when the terminal is unavailable or cannot supply market data."""


mt5_service = MT5Service()
