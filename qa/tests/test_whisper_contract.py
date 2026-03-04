from fastapi import FastAPI
from fastapi.testclient import TestClient

from whisper_chunk_api.entrypoints.http.routes import build_router


class FakeUseCase:
    def execute(self, command):
        return {
            "input_path": command.path,
            "backend": command.backend,
            "model": command.model,
            "task": command.task,
            "language": command.language,
            "chunk_seconds": command.chunk_seconds,
            "chunks_count": 1,
            "text": "ok",
            "chunks": [{"index": 0, "file": "chunk_00000.wav", "text": "ok"}],
        }


class FakeTaskRepo:
    def create_ready(self, **kwargs) -> str:
        assert kwargs["audio_path"] == "calls/call-001.mp3"
        return "task-123"


def test_transcribe_chunks_contract_shape():
    app = FastAPI()
    app.include_router(build_router(transcribe_use_case=FakeUseCase(), task_repository=FakeTaskRepo()))
    client = TestClient(app)

    response = client.post(
        "/transcribe-chunks",
        json={
            "path": "audio/input.wav",
            "model": "tiny",
            "task": "transcribe",
            "chunk_seconds": 300,
            "backend": "local",
            "cloud_model": "whisper-1",
            "temperature": 0.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(["input_path", "backend", "model", "task", "language", "chunk_seconds", "chunks_count", "text", "chunks"]).issubset(
        body.keys()
    )


def test_enqueue_whisper_task_contract_shape():
    app = FastAPI()
    app.include_router(build_router(transcribe_use_case=FakeUseCase(), task_repository=FakeTaskRepo()))
    client = TestClient(app)

    response = client.post(
        "/tasks",
        json={
            "audio_path": "calls/call-001.mp3",
            "model": "tiny",
            "task": "transcribe",
            "chunk_seconds": 300,
            "backend": "local",
            "cloud_model": "whisper-1",
            "temperature": 0.0,
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["task_id"] == "task-123"
    assert body["status"] == "ready"
