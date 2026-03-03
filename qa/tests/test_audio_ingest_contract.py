from io import BytesIO

from fastapi.testclient import TestClient

from audio_ingest_api.entrypoints.http.app import create_app


def test_audio_ingest_health_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_RUNTIME_DIR", str(tmp_path))
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_upload_creates_pending_event(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_RUNTIME_DIR", str(tmp_path))
    client = TestClient(create_app())

    response = client.post(
        "/ingest",
        data={"email": "user@example.com"},
        files={"file": ("sample.mp4", BytesIO(b"fake-video"), "video/mp4")},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["event_id"]

    status_response = client.get(f"/outbox/{body['event_id']}")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "pending"
    assert status_body["email"] == "user@example.com"
    assert status_body["source_filename"] == "sample.mp4"

