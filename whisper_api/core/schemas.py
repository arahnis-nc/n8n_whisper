from pydantic import BaseModel, Field


class TranscribeBody(BaseModel):
    path: str = Field(..., description="Path relative to records dir, e.g. my/audio.mp3")
    model: str = Field(default="turbo", description="Whisper model name")
    language: str | None = Field(default=None, description="Language code, e.g. ru, en")
    task: str = Field(default="transcribe", pattern="^(transcribe|translate)$")
    save_txt: bool = False
    save_json: bool = False
    delete_source: bool = False
    diarize: bool = False
    min_speakers: int | None = None
    max_speakers: int | None = None

