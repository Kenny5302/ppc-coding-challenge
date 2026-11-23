"""Auth, health, headers and error-handling tests."""
BODY = {"name": "x", "age": 1, "birth_state": "OH"}


def test_write_requires_api_key(client):
    assert client.post("/api/users", json=BODY).status_code == 401
    assert client.post("/api/users", json=BODY, headers={"X-API-Key": "bad"}).status_code == 403
    assert client.put("/api/users/1", json=BODY).status_code == 401
    assert client.delete("/api/users/1").status_code == 401


def test_reads_are_public(client):
    assert client.get("/api/users").status_code == 200


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "healthy", "database": "up"}


def test_openapi_available(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_request_id_and_security_headers(client):
    r = client.get("/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Request-ID" in client.get("/health").headers
