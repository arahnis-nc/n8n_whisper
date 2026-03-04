from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkTranscribeCommand:
    path: str
    model: str
    language: str | None
    task: str
    chunk_seconds: int
    backend: str
    cloud_model: str
    prompt: str | None
    temperature: float


@dataclass(frozen=True)
class WhisperTaskItem:
    id: str
    audio_path: str
    status: str
    backend: str
    model: str
    cloud_model: str
    task: str
    chunk_seconds: int
    language: str | None
    prompt: str | None
    temperature: float
    transcript_text: str | None
    transcript_json: str | None
    error: str | None = None
