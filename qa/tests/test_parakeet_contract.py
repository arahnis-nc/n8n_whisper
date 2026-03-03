from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from parakeet_api.entrypoints.http.routes import build_router


class FakeUseCase:
    def execute(self, command):
        return {
            "text": "ok",
            "model": command.model,
            "language": command.language,
            "input_path": "audio/input.wav",
        }


class FakeResolver:
    def resolve_input_file(self, relative_path: str) -> Path:
        return Path("/data/records") / relative_path


class FakeStorage:
    async def save_upload(self, filename: str | None, content: bytes) -> Path:
        return Path("/data/records/_uploads/file.wav")


def test_transcribe_json_contract_shape():
    app = FastAPI()
    app.include_router(
        build_router(
            use_case=FakeUseCase(),
            path_resolver=FakeResolver(),
            upload_storage=FakeStorage(),
        )
    )
    client = TestClient(app)

    response = client.post(
        "/transcribe",
        json={"path": "audio/input.wav", "model": "nvidia/parakeet-tdt-0.6b-v3", "delete_source": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(["text", "model", "language", "input_path"]).issubset(body.keys())
