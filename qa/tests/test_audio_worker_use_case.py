from datetime import datetime, timezone
from pathlib import Path

from audio_ingest_api.application.dto import OutboxItem
from audio_ingest_api.application.use_cases.process_outbox_item import ProcessOutboxItemUseCase


class FakeRepo:
    def __init__(self, source_filename: str = "sample.mp4"):
        self.items = {
            "evt-1": OutboxItem(
                id="evt-1",
                email="user@example.com",
                source_filename=source_filename,
                source_path="/tmp/inbox/sample.bin",
                audio_path=None,
                status="pending",
                created_at=datetime.now(timezone.utc),
                access_secret_hash="hash",
            )
        }

    def mark_processing(self, event_id: str) -> OutboxItem:
        item = self.items[event_id]
        item = OutboxItem(
            id=item.id,
            email=item.email,
            source_filename=item.source_filename,
            source_path=item.source_path,
            audio_path=item.audio_path,
            status="processing",
            created_at=item.created_at,
            access_secret_hash=item.access_secret_hash,
        )
        self.items[event_id] = item
        return item

    def mark_ready(self, event_id: str, audio_path: str) -> OutboxItem:
        item = self.items[event_id]
        item = OutboxItem(
            id=item.id,
            email=item.email,
            source_filename=item.source_filename,
            source_path=item.source_path,
            audio_path=audio_path,
            status="ready",
            created_at=item.created_at,
            access_secret_hash=item.access_secret_hash,
        )
        self.items[event_id] = item
        return item

    def mark_failed(self, event_id: str) -> OutboxItem:
        item = self.items[event_id]
        item = OutboxItem(
            id=item.id,
            email=item.email,
            source_filename=item.source_filename,
            source_path=item.source_path,
            audio_path=item.audio_path,
            status="failed",
            created_at=item.created_at,
            access_secret_hash=item.access_secret_hash,
        )
        self.items[event_id] = item
        return item


class FakeProbe:
    def __init__(self, kind: str):
        self.kind = kind

    def detect_kind(self, source_path: Path) -> str:
        return self.kind


class FakeExtractor:
    def extract_audio(self, source_path: Path, source_filename: str) -> Path:
        return Path("/tmp/processed/video.wav")


class FakeStorage:
    def persist_audio(self, source_path: Path, source_filename: str) -> Path:
        return Path("/tmp/processed/audio.mp3")


class FakeWhisperQueue:
    def __init__(self):
        self.enqueued: list[dict] = []

    def enqueue_ready_task(self, **kwargs) -> str:
        self.enqueued.append(kwargs)
        return "task-1"


def test_process_outbox_video_to_ready():
    repo = FakeRepo(source_filename="sample.mp4")
    queue = FakeWhisperQueue()
    use_case = ProcessOutboxItemUseCase(
        outbox_repository=repo,
        media_probe=FakeProbe("video"),
        audio_extractor=FakeExtractor(),
        audio_storage=FakeStorage(),
        whisper_task_queue=queue,
        whisper_backend="local",
        whisper_model="tiny",
        whisper_cloud_model="whisper-1",
        whisper_task="transcribe",
        whisper_chunk_seconds=300,
        whisper_language=None,
        whisper_prompt=None,
        whisper_temperature=0.0,
    )

    result = use_case.execute("evt-1")
    assert result.status == "ready"
    assert result.audio_path is not None
    assert result.audio_path.endswith("video.wav")
    assert len(queue.enqueued) == 1
    assert queue.enqueued[0]["audio_path"].endswith("video.wav")


def test_process_outbox_audio_to_ready():
    repo = FakeRepo(source_filename="sample.mp3")
    queue = FakeWhisperQueue()
    use_case = ProcessOutboxItemUseCase(
        outbox_repository=repo,
        media_probe=FakeProbe("audio"),
        audio_extractor=FakeExtractor(),
        audio_storage=FakeStorage(),
        whisper_task_queue=queue,
        whisper_backend="local",
        whisper_model="tiny",
        whisper_cloud_model="whisper-1",
        whisper_task="transcribe",
        whisper_chunk_seconds=300,
        whisper_language=None,
        whisper_prompt=None,
        whisper_temperature=0.0,
    )

    result = use_case.execute("evt-1")
    assert result.status == "ready"
    assert result.audio_path is not None
    assert result.audio_path.endswith("audio.mp3")
    assert len(queue.enqueued) == 1
    assert queue.enqueued[0]["audio_path"].endswith("audio.mp3")

