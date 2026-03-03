from datetime import datetime, timezone

from audio_ingest_api.application.dto import OutboxItem
from audio_ingest_api.worker import run_once


class FakeRepo:
    def list_pending(self, limit: int) -> list[OutboxItem]:
        return [
            OutboxItem(
                id="evt-1",
                email="user@example.com",
                source_filename="sample.mp4",
                source_path="/tmp/inbox/sample.mp4",
                audio_path=None,
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
        ]


class FakeUseCase:
    def __init__(self):
        self.processed = []

    def execute(self, event_id: str):
        self.processed.append(event_id)


def test_worker_polls_and_processes_pending_items(monkeypatch):
    fake_repo = FakeRepo()
    fake_use_case = FakeUseCase()

    monkeypatch.setattr(
        "audio_ingest_api.worker.build_processor",
        lambda: (fake_repo, fake_use_case),
    )

    count = run_once(limit=10)
    assert count == 1
    assert fake_use_case.processed == ["evt-1"]

