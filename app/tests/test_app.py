import os
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

from fastapi.testclient import TestClient
import main


client = TestClient(main.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-served-by"] == main.HOSTNAME


def test_version():
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {
        "version": main.APP_VERSION,
        "host": main.HOSTNAME,
    }


def test_message_escaping(monkeypatch):
    db = MagicMock()
    db.__enter__.return_value = db
    db.execute.return_value.fetchall.return_value = [
        ("<script>alert(1)</script>",),
    ]
    monkeypatch.setattr(main.psycopg, "connect", lambda url: db)

    response = client.get("/")

    assert response.status_code == 200
    assert "&lt;script&gt;" in response.text
    assert "<script>alert(1)</script>" not in response.text


def test_add_message(monkeypatch):
    db = MagicMock()
    db.__enter__.return_value = db
    monkeypatch.setattr(main.psycopg, "connect", lambda url: db)

    response = client.post(
        "/messages",
        data={"text": "Привет"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    db.execute.assert_called_once_with(
        "INSERT INTO messages (text) VALUES (%s)",
        ("Привет",),
    )
