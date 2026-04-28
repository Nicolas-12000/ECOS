from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_returns_context():
    response = client.post(
        "/api/chat",
        json={"question": "Resume la arquitectura final de ECOS y sus componentes principales."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "sources" in payload
    assert isinstance(payload["sources"], list)