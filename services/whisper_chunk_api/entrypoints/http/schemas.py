import os

from pydantic import BaseModel, Field

DEFAULT_MODEL = "tiny"
OPENAI_MODEL_DEFAULT = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")


class ChunkTranscribeBody(BaseModel):
    path: str = Field(..., description="Path relative to records dir")
    model: str = Field(default=DEFAULT_MODEL, description="Local model name for backend=local")
    language: str | None = Field(default=None)
    task: str = Field(default="transcribe", pattern="^(transcribe|translate)$")
    chunk_seconds: int = Field(default=300, ge=30, le=3600)
    backend: str = Field(default="local", pattern="^(local|cloud)$")
    cloud_model: str = Field(default=OPENAI_MODEL_DEFAULT)
    prompt: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)


class WhisperTaskCreateBody(BaseModel):
    audio_path: str = Field(..., description="Path to mp3 relative to records dir")
    model: str = Field(default=DEFAULT_MODEL, description="Local model name for backend=local")
    language: str | None = Field(default=None)
    task: str = Field(default="transcribe", pattern="^(transcribe|translate)$")
    chunk_seconds: int = Field(default=300, ge=30, le=3600)
    backend: str = Field(default="local", pattern="^(local|cloud)$")
    cloud_model: str = Field(default=OPENAI_MODEL_DEFAULT)
    prompt: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)


class WhisperTaskCreateResponse(BaseModel):
    task_id: str
    status: str = "ready"
