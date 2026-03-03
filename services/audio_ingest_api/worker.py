import os
import time
from pathlib import Path

from audio_ingest_api.application.use_cases.process_outbox_item import ProcessOutboxItemUseCase
from audio_ingest_api.infrastructure.audio_extract import FfmpegAudioExtractor
from audio_ingest_api.infrastructure.media_probe import FfprobeMediaProbe
from audio_ingest_api.infrastructure.sqlite_outbox import SqliteOutboxRepository
from audio_ingest_api.infrastructure.storage import RuntimeAudioStorage


def build_processor() -> tuple[SqliteOutboxRepository, ProcessOutboxItemUseCase]:
    runtime_audio_dir = Path(os.getenv("AUDIO_RUNTIME_DIR", "/data/audio"))
    processed_dir = runtime_audio_dir / "processed"
    outbox_db = runtime_audio_dir / "outbox.db"

    outbox_repository = SqliteOutboxRepository(outbox_db)
    outbox_repository.ensure_schema()
    use_case = ProcessOutboxItemUseCase(
        outbox_repository=outbox_repository,
        media_probe=FfprobeMediaProbe(),
        audio_extractor=FfmpegAudioExtractor(processed_dir=processed_dir),
        audio_storage=RuntimeAudioStorage(processed_dir=processed_dir),
    )
    return outbox_repository, use_case


def run_once(limit: int = 10) -> int:
    outbox_repository, use_case = build_processor()
    pending = outbox_repository.list_pending(limit=limit)
    for item in pending:
        use_case.execute(item.id)
    return len(pending)


def run_forever(poll_seconds: int = 3, limit: int = 10) -> None:
    while True:
        run_once(limit=limit)
        time.sleep(poll_seconds)


if __name__ == "__main__":
    poll_seconds = int(os.getenv("AUDIO_OUTBOX_POLL_SECONDS", "3"))
    batch_size = int(os.getenv("AUDIO_OUTBOX_BATCH_SIZE", "10"))
    run_forever(poll_seconds=poll_seconds, limit=batch_size)

