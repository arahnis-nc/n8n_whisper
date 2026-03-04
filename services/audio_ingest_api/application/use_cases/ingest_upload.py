from audio_ingest_api.application.dto import IngestResult, IngestUploadCommand
from audio_ingest_api.application.errors import ApplicationError
from audio_ingest_api.application.ports import (
    NotificationOutboxRepositoryPort,
    OutboxRepositoryPort,
    UploadStoragePort,
)
from audio_ingest_api.application.security import generate_access_secret, hash_access_secret


def _validate_email(email: str) -> str:
    trimmed = email.strip()
    if "@" not in trimmed or "." not in trimmed.split("@")[-1]:
        raise ApplicationError("Invalid email", status_code=422)
    return trimmed


class IngestUploadUseCase:
    def __init__(
        self,
        upload_storage: UploadStoragePort,
        outbox_repository: OutboxRepositoryPort,
        notification_outbox_repository: NotificationOutboxRepositoryPort,
    ):
        self._upload_storage = upload_storage
        self._outbox_repository = outbox_repository
        self._notification_outbox_repository = notification_outbox_repository

    async def execute(self, command: IngestUploadCommand) -> IngestResult:
        if not command.content:
            raise ApplicationError("File is empty", status_code=400)

        email = _validate_email(command.email)
        source_filename = command.filename or "upload.bin"
        source_path = await self._upload_storage.save_upload(source_filename, command.content)
        access_secret = generate_access_secret()
        event_id = self._outbox_repository.create_pending(
            email=email,
            source_filename=source_filename,
            source_path=str(source_path),
            access_secret_hash=hash_access_secret(access_secret),
        )
        self._notification_outbox_repository.create_pending_notification(
            event_id=event_id,
            email=email,
            access_secret=access_secret,
            source_filename=source_filename,
        )
        return IngestResult(event_id=event_id, status="pending", access_secret=access_secret)

