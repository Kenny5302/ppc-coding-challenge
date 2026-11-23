"""Unit tests for pure logic and error handlers."""
import json
import logging

import pytest
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.logging_config import JsonFormatter
from app.states import US_STATES, normalize_state


def test_state_count():
    assert len(US_STATES) == 50


@pytest.mark.parametrize("raw,code", [("oh", "OH"), (" Ohio ", "OH"), ("new  york", "NY"), ("WY", "WY")])
def test_normalize_state(raw, code):
    assert normalize_state(raw) == code


@pytest.mark.parametrize("raw", ["", "XX", "DC", "Canada"])
def test_normalize_state_invalid(raw):
    with pytest.raises(ValueError):
        normalize_state(raw)


def test_api_key_parsing():
    assert Settings(api_keys=" a, b ,,").api_key_set == {"a", "b"}


def test_json_formatter_includes_extras():
    rec = logging.LogRecord("n", logging.INFO, "f", 1, "hello", (), None)
    rec.user_id = 7
    out = json.loads(JsonFormatter().format(rec))
    assert out["msg"] == "hello" and out["user_id"] == 7 and out["level"] == "INFO"


def test_db_failure_returns_503(client, monkeypatch):
    from app import repository

    def boom(*a, **k):
        raise OperationalError("stmt", {}, Exception("down"))

    monkeypatch.setattr(repository, "list_users", boom)
    r = client.get("/api/users")
    assert r.status_code == 503 and r.json() == {"detail": "Database unavailable"}


def test_unhandled_error_returns_500_without_leak(client, monkeypatch):
    from app import repository

    monkeypatch.setattr(repository, "list_users", lambda *a, **k: 1 / 0)
    r = client.get("/api/users")
    assert r.status_code == 500 and "division" not in r.text


def test_missing_api_key_generates_random_one():
    a, b = Settings(api_keys=""), Settings(api_keys="")
    assert a.api_key_generated and len(a.api_key_set) == 1
    assert a.api_keys != b.api_keys
    assert not Settings(api_keys="x").api_key_generated


def test_generated_key_warning_never_logs_the_key(caplog):
    from app.main import warn_if_key_generated

    settings = Settings(api_keys="")
    with caplog.at_level(logging.WARNING, logger="app.main"):
        warn_if_key_generated(settings)
    assert "API_KEYS is not set" in caplog.text
    assert settings.api_keys not in caplog.text
    caplog.clear()
    warn_if_key_generated(Settings(api_keys="explicit"))
    assert caplog.text == ""
