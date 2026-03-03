from pathlib import Path

from audio_ingest_api.application.dto import ProcessResult
from audio_ingest_api.application.errors import ApplicationError
from audio_ingest_api.application.ports import (
    AudioExtractorPort,
    AudioStoragePort,
    MediaProbePort,
    OutboxRepositoryPort,
)


class ProcessOutboxItemUseCase:
    def __init__(
        self,
        outbox_repository: OutboxRepositoryPort,
        media_probe: MediaProbePort,
        audio_extractor: AudioExtractorPort,
        audio_storage: AudioStoragePort,
    ):
        self._outbox_repository = outbox_repository
        self._media_probe = media_probe
        self._audio_extractor = audio_extractor
        self._audio_storage = audio_storage

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
            return ProcessResult(
                event_id=updated.id,
                status=updated.status,
                audio_path=updated.audio_path,
            )
        except Exception:
            failed = self._outbox_repository.mark_failed(event_id)
            return ProcessResult(event_id=failed.id, status=failed.status, audio_path=failed.audio_path)

