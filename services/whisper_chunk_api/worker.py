import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from whisper_chunk_api.application.use_cases.process_task_item import ProcessWhisperTaskItemUseCase
from whisper_chunk_api.entrypoints.http.app import build_transcribe_use_case
from whisper_chunk_api.infrastructure.sqlite_tasks import SqliteWhisperTaskRepository
from whisper_chunk_api.infrastructure.summary_email_sender import (
    NoopSummaryEmailSender,
    SmtpSummaryEmailSender,
)
from whisper_chunk_api.infrastructure.text_postprocessor import (
    NoopTranscriptPostprocessor,
    OpenAiTranscriptPostprocessor,
)
from whisper_chunk_api.infrastructure.transcript_summarizer import (
    NoopTranscriptSummarizer,
    OpenAiTranscriptSummarizer,
)

logger = logging.getLogger("whisper_worker")


def build_processor() -> tuple[SqliteWhisperTaskRepository, ProcessWhisperTaskItemUseCase]:
    db_path = Path(os.getenv("WHISPER_TASKS_DB_PATH", "/data/whisper/whisper.db"))
    task_repository = SqliteWhisperTaskRepository(db_path)
    task_repository.ensure_schema()
    postprocess_enabled = os.getenv("WHISPER_TEXT_POSTPROCESS_ENABLED", "true").lower() in ("1", "true", "yes")
    if postprocess_enabled:
        model_name = os.getenv("WHISPER_TEXT_POSTPROCESS_MODEL", "gpt-5.2")
        fallback_model_name = os.getenv("WHISPER_TEXT_POSTPROCESS_FALLBACK_MODEL", "gpt-4o-mini")
        logger.info("Transcript postprocess enabled model=%s", model_name)
        postprocessor = OpenAiTranscriptPostprocessor(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=model_name,
            fallback_model=fallback_model_name,
            temperature=float(os.getenv("WHISPER_TEXT_POSTPROCESS_TEMPERATURE", "0.2")),
        )
    else:
        logger.info("Transcript postprocess disabled")
        postprocessor = NoopTranscriptPostprocessor()

    summary_enabled = os.getenv("WHISPER_SUMMARY_ENABLED", "true").lower() in ("1", "true", "yes")
    if summary_enabled:
        summary_model = os.getenv("WHISPER_SUMMARY_MODEL", "gpt-5.2")
        summary_fallback_model = os.getenv("WHISPER_SUMMARY_FALLBACK_MODEL", "gpt-4o-mini")
        logger.info("Transcript summary enabled model=%s", summary_model)
        summary_builder = OpenAiTranscriptSummarizer(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=summary_model,
            fallback_model=summary_fallback_model,
            temperature=float(os.getenv("WHISPER_SUMMARY_TEMPERATURE", "0.2")),
        )
    else:
        logger.info("Transcript summary disabled")
        summary_builder = NoopTranscriptSummarizer()

    email_enabled = os.getenv("WHISPER_SUMMARY_EMAIL_ENABLED", "true").lower() in ("1", "true", "yes")
    if email_enabled:
        logger.info("Summary email enabled via SMTP")
        try:
            summary_email_sender = SmtpSummaryEmailSender.from_env()
        except Exception:
            logger.exception("Failed to initialize summary SMTP sender; summary emails disabled")
            summary_email_sender = NoopSummaryEmailSender()
    else:
        logger.info("Summary email disabled")
        summary_email_sender = NoopSummaryEmailSender()

    use_case = ProcessWhisperTaskItemUseCase(
        task_repository=task_repository,
        transcribe_use_case=build_transcribe_use_case(),
        text_postprocessor=postprocessor,
        summary_builder=summary_builder,
        summary_email_sender=summary_email_sender,
    )
    return task_repository, use_case


def run_once(limit: int = 10) -> int:
    started_at = time.monotonic()
    task_repository, use_case = build_processor()
    logger.debug("Polling whisper queue limit=%s", limit)
    pending = task_repository.claim_ready(limit=limit)
    logger.info("Whisper poll claimed=%s limit=%s", len(pending), limit)
    for item in pending:
        task_started_at = time.monotonic()
        logger.info(
            "Processing task_id=%s path=%s backend=%s model=%s language=%s",
            item.id,
            item.audio_path,
            item.backend,
            item.cloud_model if item.backend == "cloud" else item.model,
            item.language,
        )
        result = use_case.execute(item)
        elapsed_ms = int((time.monotonic() - task_started_at) * 1000)
        if result.status == "failed":
            logger.error(
                "Task failed task_id=%s elapsed_ms=%s error=%s",
                result.id,
                elapsed_ms,
                result.error,
            )
        else:
            logger.info(
                "Task finished task_id=%s status=%s elapsed_ms=%s transcript_chars=%s",
                result.id,
                result.status,
                elapsed_ms,
                len(result.transcript_text or ""),
            )
    cycle_elapsed_ms = int((time.monotonic() - started_at) * 1000)
    logger.info(
        "Whisper cycle completed claimed=%s processed=%s elapsed_ms=%s",
        len(pending),
        len(pending),
        cycle_elapsed_ms,
    )
    return len(pending)


def run_poll_cycle(worker_count: int, limit: int) -> int:
    if worker_count <= 1:
        return run_once(limit=limit)

    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(run_once, limit) for _ in range(worker_count)]
        return sum(future.result() for future in futures)


def run_forever(*, poll_seconds: int = 3, limit: int = 10, worker_count: int = 1) -> None:
    logger.info(
        "Whisper worker started: poll_seconds=%s batch_limit=%s worker_count=%s",
        poll_seconds,
        limit,
        worker_count,
    )
    cycle_no = 0
    while True:
        cycle_no += 1
        try:
            processed = run_poll_cycle(worker_count=worker_count, limit=limit)
            if processed == 0:
                logger.debug("Whisper cycle=%s idle (no tasks)", cycle_no)
        except Exception:
            logger.exception("Unhandled whisper worker loop error")
        time.sleep(poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("WHISPER_WORKER_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    poll_seconds = int(os.getenv("WHISPER_OUTBOX_POLL_SECONDS", "3"))
    batch_size = int(os.getenv("WHISPER_OUTBOX_BATCH_SIZE", "10"))
    worker_count = max(1, int(os.getenv("WHISPER_WORKER_COUNT", "1")))
    run_forever(poll_seconds=poll_seconds, limit=batch_size, worker_count=worker_count)
