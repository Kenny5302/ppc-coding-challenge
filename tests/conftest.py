"""Test fixtures. Uses DATABASE_URL if set (Postgres in Docker/CI), else in-memory SQLite."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ["API_KEYS"] = "test-key"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

HEADERS = {"X-API-Key": "test-key"}


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def auth():
    return HEADERS


@pytest.fixture
def make_user(client):
    def _make(name="Ada Lovelace", age=36, birth_state="OH"):
        r = client.post("/api/users", json={"name": name, "age": age, "birth_state": birth_state}, headers=HEADERS)
        assert r.status_code == 201, r.text
        return r.json()

    return _make
