"""Integration tests: full HTTP -> DB round trips."""
import pytest


def test_create_and_get(client, auth):
    r = client.post("/api/users", json={"name": "  Ada  ", "age": 36, "birth_state": "ohio"}, headers=auth)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Ada" and body["birth_state"] == "OH"
    assert r.headers["Location"] == f"/api/users/{body['id']}"
    assert client.get(f"/api/users/{body['id']}").json() == body


def test_list_all(client, make_user):
    make_user("A", 20, "OH")
    make_user("B", 30, "TX")
    r = client.get("/api/users")
    assert r.status_code == 200 and len(r.json()) == 2
    assert r.headers["X-Total-Count"] == "2"


def test_update(client, make_user, auth):
    u = make_user()
    r = client.put(f"/api/users/{u['id']}", json={"name": "Grace", "age": 45, "birth_state": "NY"}, headers=auth)
    assert r.status_code == 200
    expected = {"id": u["id"], "name": "Grace", "age": 45, "birth_state": "NY"}
    assert client.get(f"/api/users/{u['id']}").json() == expected


def test_delete(client, make_user, auth):
    u = make_user()
    assert client.delete(f"/api/users/{u['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/users/{u['id']}").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"name": "", "age": 30, "birth_state": "OH"},
        {"name": "x", "age": -1, "birth_state": "OH"},
        {"name": "x", "age": 151, "birth_state": "OH"},
        {"name": "x", "age": "30", "birth_state": "OH"},
        {"name": "x", "age": 30, "birth_state": "Narnia"},
        {"name": "x", "age": 30},
        {"name": "x", "age": 30, "birth_state": "OH", "admin": True},
    ],
)
def test_create_invalid_input(client, auth, payload):
    assert client.post("/api/users", json=payload, headers=auth).status_code == 422


def test_nonexistent_user(client, auth):
    body = {"name": "x", "age": 1, "birth_state": "OH"}
    assert client.get("/api/users/999").status_code == 404
    assert client.put("/api/users/999", json=body, headers=auth).status_code == 404
    assert client.delete("/api/users/999", headers=auth).status_code == 404


def test_non_integer_id(client):
    assert client.get("/api/users/abc").status_code == 422


def test_filter_by_birth_state(client, make_user):
    make_user("A", 20, "OH")
    make_user("B", 30, "TX")
    make_user("C", 40, "OH")
    r = client.get("/api/users", params={"birth_state": "OH"})
    assert {u["name"] for u in r.json()} == {"A", "C"}
    assert r.headers["X-Total-Count"] == "2"
    assert len(client.get("/api/users", params={"birth_state": "Texas"}).json()) == 1
    assert client.get("/api/users", params={"birth_state": "WA"}).json() == []
    assert client.get("/api/users", params={"birth_state": "ZZ"}).status_code == 422


def test_pagination_and_sorting(client, make_user):
    for n, a in [("C", 30), ("A", 50), ("B", 10)]:
        make_user(n, a, "OH")
    r = client.get("/api/users", params={"sort_by": "name"})
    assert [u["name"] for u in r.json()] == ["A", "B", "C"]
    r = client.get("/api/users", params={"sort_by": "age", "order": "desc", "limit": 2})
    assert [u["age"] for u in r.json()] == [50, 30]
    assert r.headers["X-Total-Count"] == "3"
    r = client.get("/api/users", params={"sort_by": "age", "limit": 2, "offset": 2})
    assert [u["age"] for u in r.json()] == [50]
    assert client.get("/api/users", params={"sort_by": "password"}).status_code == 422
    assert client.get("/api/users", params={"limit": 0}).status_code == 422


def test_name_and_age_filters(client, make_user):
    make_user("Ann Lee", 25, "OH")
    make_user("Bob Annis", 45, "OH")
    make_user("Cy", 65, "OH")
    assert len(client.get("/api/users", params={"name": "ANN"}).json()) == 2
    r = client.get("/api/users", params={"min_age": 30, "max_age": 50})
    assert [u["name"] for u in r.json()] == ["Bob Annis"]
    assert client.get("/api/users", params={"min_age": 50, "max_age": 10}).status_code == 422
    assert client.get("/api/users", params={"name": "100%"}).json() == []
