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


class NotificationDiagnosticsResponse(BaseModel):
    total: int
    pending: int
    sending: int
    sent: int
    with_errors: int

