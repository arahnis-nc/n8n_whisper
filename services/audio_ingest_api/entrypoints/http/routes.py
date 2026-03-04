from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from audio_ingest_api.application.dto import IngestUploadCommand
from audio_ingest_api.application.errors import ApplicationError
from audio_ingest_api.application.ports import NotificationOutboxRepositoryPort, OutboxRepositoryPort
from audio_ingest_api.application.security import verify_access_secret
from audio_ingest_api.application.use_cases.ingest_upload import IngestUploadUseCase
from audio_ingest_api.entrypoints.http.schemas import (
    IngestResponse,
    NotificationDiagnosticsResponse,
    OutboxStatusResponse,
)


def build_router(
    *,
    ingest_use_case: IngestUploadUseCase,
    outbox_repository: OutboxRepositoryPort,
    notification_outbox_repository: NotificationOutboxRepositoryPort,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/ingest", response_model=IngestResponse, status_code=202)
    async def ingest(
        email: str = Form(...),
        file: UploadFile = File(...),
    ) -> IngestResponse:
        try:
            result = await ingest_use_case.execute(
                IngestUploadCommand(
                    email=email,
                    filename=file.filename,
                    content=await file.read(),
                )
            )
            return IngestResponse(event_id=result.event_id, status=result.status, secret=result.access_secret)
        except ApplicationError as err:
            raise HTTPException(status_code=err.status_code, detail=err.message) from err

    @router.get("/outbox/{event_id}/status", response_model=OutboxStatusResponse)
    def get_outbox_status(event_id: str, secret: str) -> OutboxStatusResponse:
        item = outbox_repository.get(event_id)
        if not item:
            raise HTTPException(status_code=404, detail="Outbox event not found")
        if not verify_access_secret(secret, item.access_secret_hash):
            raise HTTPException(status_code=401, detail="Invalid secret")
        return OutboxStatusResponse(
            event_id=item.id,
            status=item.status,
            audio_ready=item.audio_path is not None,
            created_at=item.created_at.isoformat(),
        )

    @router.get("/notifications/diagnostics", response_model=NotificationDiagnosticsResponse)
    def get_notification_diagnostics() -> NotificationDiagnosticsResponse:
        return NotificationDiagnosticsResponse(**notification_outbox_repository.diagnostics())

    return router

