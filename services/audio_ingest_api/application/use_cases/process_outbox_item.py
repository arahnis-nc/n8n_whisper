from pathlib import Path

from audio_ingest_api.application.dto import ProcessResult
from audio_ingest_api.application.errors import ApplicationError
from audio_ingest_api.application.ports import (
    AudioExtractorPort,
    AudioStoragePort,
    MediaProbePort,
    OutboxRepositoryPort,
    WhisperTaskQueuePort,
)


class ProcessOutboxItemUseCase:
    def __init__(
        self,
        outbox_repository: OutboxRepositoryPort,
        media_probe: MediaProbePort,
        audio_extractor: AudioExtractorPort,
        audio_storage: AudioStoragePort,
        whisper_task_queue: WhisperTaskQueuePort,
        whisper_backend: str,
        whisper_model: str,
        whisper_cloud_model: str,
        whisper_task: str,
        whisper_chunk_seconds: int,
        whisper_language: str | None,
        whisper_prompt: str | None,
        whisper_temperature: float,
    ):
        self._outbox_repository = outbox_repository
        self._media_probe = media_probe
        self._audio_extractor = audio_extractor
        self._audio_storage = audio_storage
        self._whisper_task_queue = whisper_task_queue
        self._whisper_backend = whisper_backend
        self._whisper_model = whisper_model
        self._whisper_cloud_model = whisper_cloud_model
        self._whisper_task = whisper_task
        self._whisper_chunk_seconds = whisper_chunk_seconds
        self._whisper_language = whisper_language
        self._whisper_prompt = whisper_prompt
        self._whisper_temperature = whisper_temperature

    def execute(self, event_id: str) -> ProcessResult:
        item = self._outbox_repository.mark_processing(event_id)
        source_path = Path(item.source_path)

        try:
            kind = self._media_probe.detect_kind(source_path)
            if kind == "video":
                audio_path = self._audio_extractor.extract_audio(source_path, item.source_filename)
            elif kind == "audio":
                audio_path = self._audio_storage.persist_audio(source_path, item.source_filename)
            else:
                raise ApplicationError("Unsupported media type", status_code=400)

            updated = self._outbox_repository.mark_ready(event_id, audio_path=str(audio_path))
            self._whisper_task_queue.enqueue_ready_task(
                audio_path=str(audio_path),
                backend=self._whisper_backend,
                model=self._whisper_model,
                cloud_model=self._whisper_cloud_model,
                task=self._whisper_task,
                chunk_seconds=self._whisper_chunk_seconds,
                language=self._whisper_language,
                prompt=self._whisper_prompt,
                temperature=self._whisper_temperature,
            )
            return ProcessResult(
                event_id=updated.id,
                status=updated.status,
                audio_path=updated.audio_path,
            )
        except Exception:
            failed = self._outbox_repository.mark_failed(event_id)
            return ProcessResult(event_id=failed.id, status=failed.status, audio_path=failed.audio_path)

