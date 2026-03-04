import os
import time
import logging
from pathlib import Path

from audio_ingest_api.application.use_cases.process_outbox_item import ProcessOutboxItemUseCase
from audio_ingest_api.infrastructure.audio_extract import FfmpegAudioExtractor
from audio_ingest_api.infrastructure.media_probe import FfprobeMediaProbe
from audio_ingest_api.infrastructure.sqlite_outbox import SqliteOutboxRepository
from audio_ingest_api.infrastructure.storage import RuntimeAudioStorage

logger = logging.getLogger("audio_ingest_worker")


def build_processor() -> tuple[SqliteOutboxRepository, ProcessOutboxItemUseCase]:
    runtime_audio_dir = Path(os.getenv("AUDIO_RUNTIME_DIR", "/data/audio"))
    processed_dir = runtime_audio_dir / "processed"
    outbox_db = runtime_audio_dir / "outbox" / "outbox.db"

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
    logger.info("Polling cycle: %s pending event(s), limit=%s", len(pending), limit)
    for item in pending:
        logger.info("Processing event_id=%s source=%s", item.id, item.source_filename)
        result = use_case.execute(item.id)
        logger.info(
            "Processed event_id=%s status=%s audio_path=%s",
            result.event_id,
            result.status,
            result.audio_path,
        )
    return len(pending)


def run_forever(poll_seconds: int = 3, limit: int = 10) -> None:
    logger.info("Worker started: poll_seconds=%s batch_limit=%s", poll_seconds, limit)
    while True:
        try:
            run_once(limit=limit)
        except Exception:
            logger.exception("Unhandled worker loop error")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("AUDIO_WORKER_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    poll_seconds = int(os.getenv("AUDIO_OUTBOX_POLL_SECONDS", "3"))
    batch_size = int(os.getenv("AUDIO_OUTBOX_BATCH_SIZE", "10"))
    run_forever(poll_seconds=poll_seconds, limit=batch_size)

