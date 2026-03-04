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

    def create_pending(
        self, email: str, source_filename: str, source_path: str, access_secret_hash: str
    ) -> str:
        self.last = {
            "email": email,
            "source_filename": source_filename,
            "source_path": source_path,
            "access_secret_hash": access_secret_hash,
        }
        return "evt-1"


class FakeNotificationOutboxRepository:
    def __init__(self):
        self.last = {}

    def create_pending_notification(
        self,
        *,
        event_id: str,
        email: str,
        access_secret: str,
        source_filename: str,
    ) -> str:
        self.last = {
            "event_id": event_id,
            "email": email,
            "access_secret": access_secret,
            "source_filename": source_filename,
        }
        return "ntf-1"


def test_ingest_upload_use_case_creates_pending():
    repo = FakeOutboxRepository()
    notification_repo = FakeNotificationOutboxRepository()
    use_case = IngestUploadUseCase(
        upload_storage=FakeUploadStorage(),
        outbox_repository=repo,
        notification_outbox_repository=notification_repo,
    )
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
    assert result.access_secret
    assert repo.last["email"] == "user@example.com"
    assert repo.last["source_filename"] == "sample.mp4"
    assert repo.last["access_secret_hash"]
    assert notification_repo.last["event_id"] == "evt-1"
    assert notification_repo.last["email"] == "user@example.com"
    assert notification_repo.last["source_filename"] == "sample.mp4"
    assert notification_repo.last["access_secret"] == result.access_secret

