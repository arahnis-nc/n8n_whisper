import asyncio
from pathlib import Path

from audio_ingest_api.application.dto import IngestUploadCommand
from audio_ingest_api.application.use_cases.ingest_upload import IngestUploadUseCase


class FakeUploadStorage:
    async def save_upload(self, filename: str | None, content: bytes) -> Path:
        return Path("/tmp/inbox") / (filename or "upload.bin")


class FakeOutboxRepository:
    def __init__(self):
        self.last = {}

    def create_pending(self, email: str, source_filename: str, source_path: str) -> str:
        self.last = {
            "email": email,
            "source_filename": source_filename,
            "source_path": source_path,
        }
        return "evt-1"


def test_ingest_upload_use_case_creates_pending():
    repo = FakeOutboxRepository()
    use_case = IngestUploadUseCase(upload_storage=FakeUploadStorage(), outbox_repository=repo)
    result = asyncio.run(
        use_case.execute(
            IngestUploadCommand(
                email="user@example.com",
                filename="sample.mp4",
                content=b"data",
            )
        )
    )

    assert result.event_id == "evt-1"
    assert result.status == "pending"
    assert repo.last["email"] == "user@example.com"
    assert repo.last["source_filename"] == "sample.mp4"

