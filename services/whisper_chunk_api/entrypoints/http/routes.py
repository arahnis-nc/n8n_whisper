from fastapi import APIRouter, HTTPException

from whisper_chunk_api.application.dto import ChunkTranscribeCommand
from whisper_chunk_api.application.errors import ApplicationError
from whisper_chunk_api.application.use_cases.transcribe_chunks import TranscribeChunksUseCase
from whisper_chunk_api.entrypoints.http.schemas import ChunkTranscribeBody


def build_router(use_case: TranscribeChunksUseCase) -> APIRouter:
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
            return use_case.execute(command)
        except ApplicationError as err:
            raise HTTPException(status_code=err.status_code, detail=err.message) from err

    return router
