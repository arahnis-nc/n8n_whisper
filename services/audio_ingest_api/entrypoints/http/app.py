import os
from pathlib import Path

from fastapi import FastAPI

from audio_ingest_api.application.use_cases.ingest_upload import IngestUploadUseCase
from audio_ingest_api.entrypoints.http.routes import build_router
from audio_ingest_api.infrastructure.sqlite_outbox import (
    SqliteNotificationOutboxRepository,
    SqliteOutboxRepository,
)
from audio_ingest_api.infrastructure.storage import LocalUploadStorage


def create_app() -> FastAPI:
    runtime_audio_dir = Path(os.getenv("AUDIO_RUNTIME_DIR", "/data/audio"))
    inbox_dir = runtime_audio_dir / "inbox"
    outbox_db = runtime_audio_dir / "outbox" / "outbox.db"

    upload_storage = LocalUploadStorage(inbox_dir)
    outbox_repository = SqliteOutboxRepository(outbox_db)
    notification_outbox_repository = SqliteNotificationOutboxRepository(outbox_db)
    outbox_repository.ensure_schema()
    notification_outbox_repository.ensure_schema()
    ingest_use_case = IngestUploadUseCase(
        upload_storage=upload_storage,
        outbox_repository=outbox_repository,
        notification_outbox_repository=notification_outbox_repository,
    )

    app = FastAPI(title="Audio Ingest API", version="1.0.0")
    app.include_router(
        build_router(
            ingest_use_case=ingest_use_case,
            outbox_repository=outbox_repository,
            notification_outbox_repository=notification_outbox_repository,
        )
    )
    return app

