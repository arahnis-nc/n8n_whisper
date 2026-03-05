import logging
import os
import time
from pathlib import Path

from audio_ingest_api.application.use_cases.process_notification_item import ProcessNotificationItemUseCase
from audio_ingest_api.infrastructure.smtp_sender import SmtpEmailSender
from audio_ingest_api.infrastructure.sqlite_outbox import SqliteNotificationOutboxRepository

logger = logging.getLogger("audio_notify_worker")


def build_processor() -> tuple[SqliteNotificationOutboxRepository, ProcessNotificationItemUseCase]:
    runtime_audio_dir = Path(os.getenv("AUDIO_RUNTIME_DIR", "/data/audio"))
    outbox_db = runtime_audio_dir / "outbox" / "outbox.db"

    notification_repository = SqliteNotificationOutboxRepository(outbox_db)
    notification_repository.ensure_schema()
    sender = SmtpEmailSender.from_env()
    use_case = ProcessNotificationItemUseCase(notification_repository=notification_repository, sender=sender)
    return notification_repository, use_case


def run_once(limit: int = 10) -> int:
    notification_repository, use_case = build_processor()
    pending = notification_repository.list_pending(limit=limit)
    logger.info("Notification poll: %s pending item(s), limit=%s", len(pending), limit)
    for item in pending:
        logger.info(
            "Sending notification id=%s event_id=%s email=%s attempt=%s",
            item.id,
            item.event_id,
            item.email,
            item.attempts + 1,
        )
        result = use_case.execute(item.id)
        logger.info(
            "Notification processed id=%s status=%s attempts=%s last_error=%s",
            result.id,
            result.status,
            result.attempts,
            result.last_error,
        )
    return len(pending)


def run_forever(poll_seconds: int = 3, limit: int = 10) -> None:
    logger.info("Notification worker started: poll_seconds=%s batch_limit=%s", poll_seconds, limit)
    while True:
        try:
            run_once(limit=limit)
        except Exception:
            logger.exception("Unhandled notification worker loop error")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("AUDIO_NOTIFY_WORKER_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    poll_seconds = int(os.getenv("AUDIO_NOTIFY_POLL_SECONDS", "5"))
    batch_size = int(os.getenv("AUDIO_NOTIFY_BATCH_SIZE", "10"))
    run_forever(poll_seconds=poll_seconds, limit=batch_size)
