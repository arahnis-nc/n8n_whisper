from pydantic import BaseModel


class IngestResponse(BaseModel):
    event_id: str
    status: str


class OutboxStatusResponse(BaseModel):
    id: str
    email: str
    source_filename: str
    source_path: str
    audio_path: str | None
    status: str
    created_at: str

