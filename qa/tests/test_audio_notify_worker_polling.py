from datetime import datetime, timezone

from audio_ingest_api.application.dto import NotificationOutboxItem
from audio_ingest_api.notification_worker import run_once


class FakeNotificationRepo:
    def list_pending(self, limit: int) -> list[NotificationOutboxItem]:
        return [
            NotificationOutboxItem(
                id="ntf-1",
                event_id="evt-1",
                email="user@example.com",
                access_secret="sec-1",
                source_filename="sample.mp4",
                status="pending",
                attempts=0,
                last_error=None,
                created_at=datetime.now(timezone.utc),
                sent_at=None,
            )
        ]


class FakeUseCase:
    def __init__(self):
        self.processed = []

    def execute(self, notification_id: str):
        self.processed.append(notification_id)
        return type(
            "Result",
            (),
            {"id": notification_id, "status": "sent", "attempts": 0, "last_error": None},
        )()


def test_notify_worker_polls_and_processes_pending_items(monkeypatch):
    fake_repo = FakeNotificationRepo()
    fake_use_case = FakeUseCase()

    monkeypatch.setattr(
        "audio_ingest_api.notification_worker.build_processor",
        lambda: (fake_repo, fake_use_case),
    )

    count = run_once(limit=10)
    assert count == 1
    assert fake_use_case.processed == ["ntf-1"]
