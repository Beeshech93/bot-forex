from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.services import mt5_service as mt5_module
from app.services.mt5_service import MT5Service, MT5UnavailableError
from app.services.market_service import InsufficientMarketDataError, calculate_indicators
from app.strategies.ema_rsi_atr import StrategyConfig, generate_signal
from app.backtesting.engine import BacktestRequest, run_backtest
from app.api import backtest as backtest_api
from app.api import signals as signals_api
from datetime import datetime, timedelta, timezone
import pytest

client = TestClient(app)
client.__enter__()
VALID_TOKEN = "t" * 40


def teardown_module() -> None:
    client.__exit__(None, None, None)


def setup_function() -> None:
    get_settings.cache_clear()


def test_health_is_public_and_contains_no_sensitive_details() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "smart-signals-fx-api"}
    assert "X-Request-ID" in response.headers


def test_health_echoes_valid_request_id() -> None:
    response = client.get("/health", headers={"X-Request-ID": "trace-123"})
    assert response.headers["X-Request-ID"] == "trace-123"


def test_health_replaces_unsafe_request_id() -> None:
    response = client.get("/health", headers={"X-Request-ID": "bad id\r\n"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "bad id\r\n"


def test_protected_route_requires_token(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    response = client.get("/api/v1/terminal")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_route_rejects_wrong_token(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    response = client.get("/api/v1/terminal", headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_protected_route_accepts_configured_token(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    response = client.get("/api/v1/terminal", headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    assert response.status_code == 200
    assert response.json()["status"] == "disconnected"


def test_protected_route_fails_closed_without_token(monkeypatch) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_settings.cache_clear()
    response = client.get("/api/v1/terminal")
    assert response.status_code == 503


class FakeMT5:
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    def __init__(self, connected: bool = True) -> None:
        self.connected = connected

    def terminal_info(self):
        return type("Terminal", (), {"connected": self.connected})()

    def account_info(self):
        return object() if self.connected else None

    def symbols_get(self):
        return [type("Symbol", (), {"name": "EURUSD.a", "description": "Euro vs US Dollar", "visible": True})()]

    def last_error(self):
        return (0, "ok")

    def shutdown(self):
        pass

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.copy_request = (symbol, timeframe, start_pos, count)
        base = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())
        return [{"time": base, "open": 1.0, "high": 1.2, "low": 0.9, "close": 1.1,
                 "tick_volume": 20, "spread": 3, "real_volume": 0}]


def test_mt5_status_does_not_expose_account_details(monkeypatch) -> None:
    monkeypatch.setattr(mt5_module.platform, "system", lambda: "Windows")
    result = MT5Service(FakeMT5()).status()
    assert result.connected is True
    assert "account" not in result.message.lower()


def test_mt5_symbols_keep_broker_symbol_name(monkeypatch) -> None:
    monkeypatch.setattr(mt5_module.platform, "system", lambda: "Windows")
    service = MT5Service(FakeMT5())
    assert service.symbols() == [{"name": "EURUSD.a", "description": "Euro vs US Dollar", "visible": True}]


def test_mt5_symbols_raise_when_disconnected(monkeypatch) -> None:
    monkeypatch.setattr(mt5_module.platform, "system", lambda: "Windows")
    service = MT5Service(FakeMT5(connected=False))
    try:
        service.symbols()
    except MT5UnavailableError:
        pass
    else:
        raise AssertionError("expected a disconnected terminal to be unavailable")


def test_terminal_endpoint_requires_auth_and_reports_status(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    monkeypatch.setattr(mt5_module.mt5_service, "status", lambda: type("S", (), {
        "connected": False, "available": False, "platform_supported": False, "message": "MetaTrader 5 requires Windows"
    })())
    response = client.get("/api/v1/terminal", headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    assert response.status_code == 200
    assert response.json()["status"] == "disconnected"


def test_mt5_candles_start_at_shift_one_to_exclude_open_bar(monkeypatch) -> None:
    monkeypatch.setattr(mt5_module.platform, "system", lambda: "Windows")
    fake = FakeMT5()
    rows = MT5Service(fake).candles("EURUSD.a", "M5", 120)
    assert fake.copy_request == ("EURUSD.a", 5, 1, 120)
    assert rows[0]["time"].tzinfo == timezone.utc


def _candles(closes: list[float]) -> list[dict]:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    output = []
    for index, close in enumerate(closes):
        output.append({"time": start + timedelta(minutes=5 * index), "open": close,
                       "high": close + 1, "low": close - 1, "close": close})
    return output


def test_indicator_values_are_calculated_for_closed_candles() -> None:
    frame = calculate_indicators(_candles([float(value) for value in range(1, 61)]))
    latest = frame.iloc[-1]
    assert latest["ema_fast"] > latest["ema_slow"]
    assert latest["rsi"] == pytest.approx(100.0)
    assert latest["atr"] == pytest.approx(2.0)


def test_indicator_calculation_rejects_insufficient_history() -> None:
    with pytest.raises(InsufficientMarketDataError):
        calculate_indicators(_candles([1.0] * 20))


def test_market_endpoint_validates_symbol_and_limit(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    invalid_symbol = client.get("/api/v1/candles?symbol=EUR%2FUSD&timeframe=M5&limit=10",
                               headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    excessive_limit = client.get("/api/v1/candles?symbol=EURUSD&timeframe=M5&limit=1001",
                                headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    assert invalid_symbol.status_code == 422
    assert excessive_limit.status_code == 422


def test_strategy_generates_buy_with_theoretical_levels() -> None:
    closes = [float(value) for value in range(1, 101)] + [80.0, 110.0]
    config = StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3)
    result = generate_signal("EURUSD", "M5", _candles(closes), config)
    assert result.direction == "BUY"
    assert result.stop_loss < result.reference_price < result.take_profit
    assert result.reward_risk == 2.0


def test_strategy_generates_sell_with_theoretical_levels() -> None:
    closes = [float(value) for value in range(200, 100, -1)] + [120.0, 80.0]
    config = StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3)
    result = generate_signal("EURUSD", "M15", _candles(closes), config)
    assert result.direction == "SELL"
    assert result.take_profit < result.reference_price < result.stop_loss


def test_strategy_returns_no_signal_for_flat_market() -> None:
    config = StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3)
    result = generate_signal("EURUSD", "M5", _candles([10.0] * 30), config)
    assert result.direction == "NO_SIGNAL"
    assert result.data_valid is True


def test_strategy_returns_no_signal_when_data_is_insufficient() -> None:
    config = StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3)
    result = generate_signal("EURUSD", "M5", _candles([10.0, 11.0]), config)
    assert result.direction == "NO_SIGNAL"
    assert result.data_valid is False


def test_backtest_enters_on_the_next_candle_and_stops_first_when_both_levels_hit() -> None:
    closes = [float(value) for value in range(1, 101)] + [91.0, 110.0, 110.0]
    candles = _candles(closes)
    strategy = StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3,
                              stop_atr_multiple=0.1)
    request = BacktestRequest(symbol="EURUSD", timeframe="M5", start_date=candles[0]["time"],
                              end_date=candles[-1]["time"], strategy=strategy)
    result = run_backtest(candles, request)
    assert result.trade_count > 0
    trade = result.trades[0]
    assert trade.entry_time == candles[102]["time"]
    assert trade.exit_reason == "stop_loss"
    assert trade.result == "loss"


def test_backtest_does_not_use_future_candle_to_create_signal() -> None:
    closes = [float(value) for value in range(1, 101)] + [91.0, 110.0]
    candles = _candles(closes)
    request = BacktestRequest(
        symbol="EURUSD", timeframe="M5", start_date=candles[0]["time"], end_date=candles[-1]["time"],
        strategy=StrategyConfig(ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3),
    )
    assert run_backtest(candles, request).trade_count == 0


def test_strategy_configuration_is_persisted_and_validated(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    current = client.get("/api/v1/config", headers=headers)
    assert current.status_code == 200
    config = current.json()
    config["rsi_buy_min"] = 60.0
    updated = client.put("/api/v1/config", json=config, headers=headers)
    assert updated.status_code == 200
    assert client.get("/api/v1/config", headers=headers).json()["rsi_buy_min"] == 60.0
    invalid = {**config, "ema_fast": 60, "ema_slow": 50}
    assert client.put("/api/v1/config", json=invalid, headers=headers).status_code == 422
    client.put("/api/v1/config", json={**config, "rsi_buy_min": 55.0}, headers=headers)


def test_signal_history_and_metrics_are_authenticated(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    assert client.get("/api/v1/signals/history").status_code == 401
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    history = client.get("/api/v1/signals/history", headers=headers)
    metrics = client.get("/api/v1/metrics", headers=headers)
    assert history.status_code == 200
    assert "items" in history.json()
    assert metrics.status_code == 200
    assert "by_symbol_timeframe" in metrics.json()


def test_signal_endpoint_persists_one_record_per_closed_candle(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    candles = _candles([float(value) for value in range(1, 101)] + [91.0, 150.0])
    monkeypatch.setattr(signals_api.market_service, "get_closed_candles", lambda *args: candles)
    monkeypatch.setattr(signals_api, "current_strategy_config", lambda db: StrategyConfig(
        ema_fast=5, ema_slow=10, rsi_period=3, atr_period=3))
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    first = client.get("/api/v1/signals?symbol=TESTEUR&timeframe=M5", headers=headers)
    again = client.get("/api/v1/signals?symbol=TESTEUR&timeframe=M5", headers=headers)
    history = client.get("/api/v1/signals/history?limit=500", headers=headers).json()["items"]
    assert first.status_code == 200
    assert first.json()["direction"] == "BUY"
    assert again.status_code == 200
    assert sum(item["symbol"] == "TESTEUR" for item in history) == 1


def test_backtest_api_persists_result_id(monkeypatch) -> None:
    monkeypatch.setenv("API_TOKEN", VALID_TOKEN)
    get_settings.cache_clear()
    candles = _candles([float(value) for value in range(1, 101)] + [91.0, 110.0, 110.0])
    monkeypatch.setattr(backtest_api.mt5_service, "candles_between", lambda *args: candles)
    payload = {
        "symbol": "TESTEUR", "timeframe": "M5",
        "start_date": candles[0]["time"].isoformat(), "end_date": candles[-1]["time"].isoformat(),
        "strategy": {"ema_fast": 5, "ema_slow": 10, "rsi_period": 3, "atr_period": 3,
                     "stop_atr_multiple": 0.1},
    }
    headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
    created = client.post("/api/v1/backtest", json=payload, headers=headers)
    assert created.status_code == 200
    result_id = created.json()["id"]
    fetched = client.get(f"/api/v1/backtest/{result_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["result"]["symbol"] == "TESTEUR"
