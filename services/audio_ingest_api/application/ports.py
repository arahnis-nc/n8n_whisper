from pathlib import Path
from typing import Protocol

from audio_ingest_api.application.dto import MediaKind, NotificationOutboxItem, OutboxItem


class UploadStoragePort(Protocol):
    async def save_upload(self, filename: str | None, content: bytes) -> Path: ...


class OutboxRepositoryPort(Protocol):
    def ensure_schema(self) -> None: ...

    def create_pending(
        self, email: str, source_filename: str, source_path: str, access_secret_hash: str
    ) -> str: ...

    def list_pending(self, limit: int) -> list[OutboxItem]: ...

    def mark_processing(self, event_id: str) -> OutboxItem: ...

    def mark_ready(self, event_id: str, audio_path: str) -> OutboxItem: ...

    def mark_failed(self, event_id: str) -> OutboxItem: ...

    def get(self, event_id: str) -> OutboxItem | None: ...


class MediaProbePort(Protocol):
    def detect_kind(self, source_path: Path) -> MediaKind: ...


class AudioExtractorPort(Protocol):
    def extract_audio(self, source_path: Path, source_filename: str) -> Path: ...


class AudioStoragePort(Protocol):
    def persist_audio(self, source_path: Path, source_filename: str) -> Path: ...


class NotificationOutboxRepositoryPort(Protocol):
    def ensure_schema(self) -> None: ...

    def create_pending_notification(
        self,
        *,
        event_id: str,
        email: str,
        access_secret: str,
        source_filename: str,
    ) -> str: ...

    def list_pending(self, limit: int) -> list[NotificationOutboxItem]: ...

    def mark_sending(self, notification_id: str) -> NotificationOutboxItem: ...

    def mark_sent(self, notification_id: str) -> NotificationOutboxItem: ...

    def mark_retry(self, notification_id: str, error_message: str) -> NotificationOutboxItem: ...

    def get(self, notification_id: str) -> NotificationOutboxItem | None: ...

    def diagnostics(self) -> dict[str, int]: ...


class EmailSenderPort(Protocol):
    def send(self, *, recipient: str, subject: str, body: str) -> None: ...


class WhisperTaskQueuePort(Protocol):
    def enqueue_ready_task(
        self,
        *,
        audio_path: str,
        backend: str,
        model: str,
        cloud_model: str,
        task: str,
        chunk_seconds: int,
        language: str | None,
        prompt: str | None,
        temperature: float,
    ) -> str: ...

