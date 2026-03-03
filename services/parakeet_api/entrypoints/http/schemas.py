from pydantic import BaseModel, Field

DEFAULT_MODEL = "nvidia/parakeet-tdt-0.6b-v3"


class TranscribeBody(BaseModel):
    path: str = Field(..., description="Path relative to records dir, e.g. audio/test.mp4")
    model: str = Field(default=DEFAULT_MODEL)
    language: str | None = Field(default=None)
    delete_source: bool = False
