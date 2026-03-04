from dataclasses import dataclass
from datetime import datetime
from typing import Literal

OutboxStatus = Literal["pending", "processing", "ready", "failed"]
NotificationStatus = Literal["pending", "sending", "sent"]
MediaKind = Literal["video", "audio", "unknown"]


@dataclass(frozen=True)
class IngestUploadCommand:
    email: str
    filename: str | None
    content: bytes


@dataclass(frozen=True)
class IngestResult:
    event_id: str
    status: OutboxStatus
    access_secret: str


@dataclass(frozen=True)
class OutboxItem:
    id: str
    email: str
    source_filename: str
    source_path: str
    audio_path: str | None
    status: OutboxStatus
    created_at: datetime
    access_secret_hash: str


@dataclass(frozen=True)
class ProcessResult:
    event_id: str
    status: OutboxStatus
    audio_path: str | None


@dataclass(frozen=True)
class NotificationOutboxItem:
    id: str
    event_id: str
    email: str
    access_secret: str
    source_filename: str
    status: NotificationStatus
    attempts: int
    last_error: str | None
    created_at: datetime
    sent_at: datetime | None


@dataclass(frozen=True)
class NotificationProcessResult:
    id: str
    status: NotificationStatus
    attempts: int
    last_error: str | None

