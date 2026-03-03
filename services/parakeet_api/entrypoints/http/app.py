from pathlib import Path

from fastapi import FastAPI

from parakeet_api.application.use_cases.transcribe_audio import TranscribeAudioUseCase
from parakeet_api.entrypoints.http.routes import build_router
from parakeet_api.infrastructure.storage import LocalUploadStorage, RecordsPathResolver
from parakeet_api.infrastructure.transcriber import NemoParakeetTranscriber


def create_app() -> FastAPI:
    records_dir = Path("/data/records")
    uploads_dir = records_dir / "_uploads"
    path_resolver = RecordsPathResolver(records_dir)
    upload_storage = LocalUploadStorage(uploads_dir)
    use_case = TranscribeAudioUseCase(
        transcriber=NemoParakeetTranscriber(device="cpu"),
        path_resolver=path_resolver,
        upload_storage=upload_storage,
    )

    app = FastAPI(title="Parakeet API", version="1.0.0")
    app.include_router(
        build_router(
            use_case=use_case,
            path_resolver=path_resolver,
            upload_storage=upload_storage,
        )
    )
    return app
