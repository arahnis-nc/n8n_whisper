import os
from pathlib import Path

from fastapi import FastAPI

from whisper_chunk_api.application.use_cases.transcribe_chunks import TranscribeChunksUseCase
from whisper_chunk_api.entrypoints.http.routes import build_router
from whisper_chunk_api.infrastructure.chunker import FfmpegChunker
from whisper_chunk_api.infrastructure.storage import RecordsPathResolver, TempWorkspace
from whisper_chunk_api.infrastructure.transcriber import BackendAwareTranscriber


def create_app() -> FastAPI:
    records_dir = Path("/data/records")
    transcriber = BackendAwareTranscriber(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        local_device="cpu",
    )
    use_case = TranscribeChunksUseCase(
        path_resolver=RecordsPathResolver(records_dir),
        chunker=FfmpegChunker(),
        transcriber=transcriber,
        workspace=TempWorkspace(),
    )

    app = FastAPI(title="Whisper Chunk API", version="1.0.0")
    app.include_router(build_router(use_case))
    return app
