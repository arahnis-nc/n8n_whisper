import os
from pathlib import Path

from fastapi import FastAPI

from whisper_chunk_api.application.use_cases.transcribe_chunks import TranscribeChunksUseCase
from whisper_chunk_api.entrypoints.http.routes import build_router
from whisper_chunk_api.infrastructure.chunker import FfmpegChunker
from whisper_chunk_api.infrastructure.sqlite_tasks import SqliteWhisperTaskRepository
from whisper_chunk_api.infrastructure.storage import RecordsPathResolver, TempWorkspace
from whisper_chunk_api.infrastructure.transcriber import BackendAwareTranscriber


def build_transcribe_use_case() -> TranscribeChunksUseCase:
    records_dir = Path("/data/records")
    allowed_dirs_raw = os.getenv("WHISPER_ALLOWED_INPUT_DIRS", "/data/records,/data/audio/processed")
    allowed_dirs = [Path(item.strip()) for item in allowed_dirs_raw.split(",") if item.strip()]
    transcriber = BackendAwareTranscriber(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        local_device="cpu",
    )
    use_case = TranscribeChunksUseCase(
        path_resolver=RecordsPathResolver(records_dir, allowed_input_dirs=allowed_dirs),
        chunker=FfmpegChunker(),
        transcriber=transcriber,
        workspace=TempWorkspace(),
    )
    return use_case


def create_app() -> FastAPI:
    transcribe_use_case = build_transcribe_use_case()
    task_repository = SqliteWhisperTaskRepository(
        Path(os.getenv("WHISPER_TASKS_DB_PATH", "/data/whisper/whisper.db"))
    )
    task_repository.ensure_schema()

    app = FastAPI(title="Whisper Chunk API", version="1.0.0")
    app.include_router(build_router(transcribe_use_case=transcribe_use_case, task_repository=task_repository))
    return app
