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
