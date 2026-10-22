from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)
VALID_TOKEN = "t" * 40


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
    assert response.json()["status"] == "not_configured"


def test_protected_route_fails_closed_without_token(monkeypatch) -> None:
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_settings.cache_clear()
    response = client.get("/api/v1/terminal")
    assert response.status_code == 503
