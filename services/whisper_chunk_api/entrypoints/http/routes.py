from fastapi import APIRouter, HTTPException

from whisper_chunk_api.application.dto import ChunkTranscribeCommand
from whisper_chunk_api.application.errors import ApplicationError
from whisper_chunk_api.application.use_cases.transcribe_chunks import TranscribeChunksUseCase
from whisper_chunk_api.entrypoints.http.schemas import (
    ChunkTranscribeBody,
    WhisperTaskCreateBody,
    WhisperTaskCreateResponse,
)


def build_router(*, transcribe_use_case: TranscribeChunksUseCase, task_repository) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/transcribe-chunks")
    def transcribe_chunks(body: ChunkTranscribeBody):
        command = ChunkTranscribeCommand(
            path=body.path,
            model=body.model,
            language=body.language,
            task=body.task,
            chunk_seconds=body.chunk_seconds,
            backend=body.backend,
            cloud_model=body.cloud_model,
            prompt=body.prompt,
            temperature=body.temperature,
        )
        try:
            return transcribe_use_case.execute(command)
        except ApplicationError as err:
            raise HTTPException(status_code=err.status_code, detail=err.message) from err

    @router.post("/tasks", response_model=WhisperTaskCreateResponse, status_code=202)
    def create_task(body: WhisperTaskCreateBody) -> WhisperTaskCreateResponse:
        task_id = task_repository.create_ready(
            audio_path=body.audio_path,
            backend=body.backend,
            model=body.model,
            cloud_model=body.cloud_model,
            task=body.task,
            chunk_seconds=body.chunk_seconds,
            language=body.language,
            prompt=body.prompt,
            temperature=body.temperature,
        )
        return WhisperTaskCreateResponse(task_id=task_id, status="ready")

    return router
