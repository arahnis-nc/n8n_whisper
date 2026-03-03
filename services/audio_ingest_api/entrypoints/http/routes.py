from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from audio_ingest_api.application.dto import IngestUploadCommand
from audio_ingest_api.application.errors import ApplicationError
from audio_ingest_api.application.ports import OutboxRepositoryPort
from audio_ingest_api.application.use_cases.ingest_upload import IngestUploadUseCase
from audio_ingest_api.entrypoints.http.schemas import IngestResponse, OutboxStatusResponse


def build_router(
    *,
    ingest_use_case: IngestUploadUseCase,
    outbox_repository: OutboxRepositoryPort,
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
            return IngestResponse(event_id=result.event_id, status=result.status)
        except ApplicationError as err:
            raise HTTPException(status_code=err.status_code, detail=err.message) from err

    @router.get("/outbox/{event_id}", response_model=OutboxStatusResponse)
    def get_outbox_status(event_id: str) -> OutboxStatusResponse:
        item = outbox_repository.get(event_id)
        if not item:
            raise HTTPException(status_code=404, detail="Outbox event not found")
        return OutboxStatusResponse(
            id=item.id,
            email=item.email,
            source_filename=item.source_filename,
            source_path=item.source_path,
            audio_path=item.audio_path,
            status=item.status,
            created_at=item.created_at.isoformat(),
        )

    return router

