from dataclasses import dataclass
from datetime import datetime
from typing import Literal

OutboxStatus = Literal["pending", "processing", "ready", "failed"]
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


@dataclass(frozen=True)
class OutboxItem:
    id: str
    email: str
    source_filename: str
    source_path: str
    audio_path: str | None
    status: OutboxStatus
    created_at: datetime


@dataclass(frozen=True)
class ProcessResult:
    event_id: str
    status: OutboxStatus
    audio_path: str | None

