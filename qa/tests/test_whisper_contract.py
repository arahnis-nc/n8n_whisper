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


def test_transcribe_chunks_contract_shape():
    app = FastAPI()
    app.include_router(build_router(FakeUseCase()))
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
