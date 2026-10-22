"""Durable application records. JSON payloads contain analysis results only."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SignalRecord(Base):
    __tablename__ = "signal_history"
    __table_args__ = (UniqueConstraint("symbol", "timeframe", "candle_time", name="uq_signal_candle"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(3), index=True)
    candle_time: Mapped[str] = mapped_column(String(40))
    direction: Mapped[str] = mapped_column(String(10), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class BacktestRecord(Base):
    __tablename__ = "backtest_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(3), index=True)
    trade_count: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class StrategyConfigRecord(Base):
    __tablename__ = "strategy_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    payload: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class TechnicalEventRecord(Base):
    __tablename__ = "technical_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    message: Mapped[str] = mapped_column(String(500))
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
