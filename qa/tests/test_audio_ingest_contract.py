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
    assert body["secret"]

    status_response = client.get(f"/outbox/{body['event_id']}/status", params={"secret": body["secret"]})
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "pending"
    assert status_body["event_id"] == body["event_id"]
    assert status_body["audio_ready"] is False
    assert "whisper_task_id" in status_body
    assert "whisper_status" in status_body
    assert "whisper_transcript" in status_body
    assert "whisper_raw_text" in status_body
    assert "whisper_formatted_text" in status_body
    assert "whisper_error" in status_body


def test_outbox_status_requires_valid_secret(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_RUNTIME_DIR", str(tmp_path))
    client = TestClient(create_app())

    ingest_response = client.post(
        "/ingest",
        data={"email": "user@example.com"},
        files={"file": ("sample.mp4", BytesIO(b"fake-video"), "video/mp4")},
    )
    assert ingest_response.status_code == 202
    event_id = ingest_response.json()["event_id"]

    forbidden_response = client.get(f"/outbox/{event_id}/status", params={"secret": "wrong-secret"})
    assert forbidden_response.status_code == 401


def test_notification_diagnostics_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_RUNTIME_DIR", str(tmp_path))
    client = TestClient(create_app())

    ingest_response = client.post(
        "/ingest",
        data={"email": "user@example.com"},
        files={"file": ("sample.mp4", BytesIO(b"fake-video"), "video/mp4")},
    )
    assert ingest_response.status_code == 202

    diagnostics = client.get("/notifications/diagnostics")
    assert diagnostics.status_code == 200
    body = diagnostics.json()
    assert body["total"] >= 1
    assert body["pending"] >= 1
    assert body["sending"] >= 0
    assert body["sent"] >= 0
    assert body["with_errors"] >= 0

