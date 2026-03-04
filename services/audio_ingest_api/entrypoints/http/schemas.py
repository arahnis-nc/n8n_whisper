from pydantic import BaseModel


class IngestResponse(BaseModel):
    event_id: str
    status: str
    secret: str


class OutboxStatusResponse(BaseModel):
    event_id: str
    status: str
    audio_ready: bool
    created_at: str
    whisper_task_id: str | None = None
    whisper_status: str | None = None
    whisper_transcript: str | None = None
    whisper_raw_text: str | None = None
    whisper_formatted_text: str | None = None
    whisper_error: str | None = None


class NotificationDiagnosticsResponse(BaseModel):
    total: int
    pending: int
    sending: int
    sent: int
    with_errors: int

