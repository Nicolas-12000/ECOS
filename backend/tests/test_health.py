from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload.get("database") in {None, "ok", "error"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"name": "ECOS API", "status": "ok"}
