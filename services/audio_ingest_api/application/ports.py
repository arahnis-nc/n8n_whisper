from pathlib import Path
from typing import Protocol

from audio_ingest_api.application.dto import MediaKind, OutboxItem


class UploadStoragePort(Protocol):
    async def save_upload(self, filename: str | None, content: bytes) -> Path: ...


class OutboxRepositoryPort(Protocol):
    def ensure_schema(self) -> None: ...

    def create_pending(self, email: str, source_filename: str, source_path: str) -> str: ...

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

