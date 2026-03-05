from datetime import datetime, timezone

from audio_ingest_api.application.dto import NotificationOutboxItem
from audio_ingest_api.application.use_cases.process_notification_item import ProcessNotificationItemUseCase


class FakeNotificationRepo:
    def __init__(self):
        created_at = datetime.now(timezone.utc)
        self.items = {
            "ntf-1": NotificationOutboxItem(
                id="ntf-1",
                event_id="evt-1",
                email="user@example.com",
                access_secret="sec-1",
                source_filename="sample.mp4",
                status="pending",
                attempts=0,
                last_error=None,
                created_at=created_at,
                sent_at=None,
            )
        }

    def mark_sending(self, notification_id: str) -> NotificationOutboxItem:
        item = self.items[notification_id]
        item = NotificationOutboxItem(
            id=item.id,
            event_id=item.event_id,
            email=item.email,
            access_secret=item.access_secret,
            source_filename=item.source_filename,
            status="sending",
            attempts=item.attempts,
            last_error=item.last_error,
            created_at=item.created_at,
            sent_at=item.sent_at,
        )
        self.items[notification_id] = item
        return item

    def mark_sent(self, notification_id: str) -> NotificationOutboxItem:
        item = self.items[notification_id]
        item = NotificationOutboxItem(
            id=item.id,
            event_id=item.event_id,
            email=item.email,
            access_secret=item.access_secret,
            source_filename=item.source_filename,
            status="sent",
            attempts=item.attempts,
            last_error=item.last_error,
            created_at=item.created_at,
            sent_at=datetime.now(timezone.utc),
        )
        self.items[notification_id] = item
        return item

    def mark_retry(self, notification_id: str, error_message: str) -> NotificationOutboxItem:
        item = self.items[notification_id]
        item = NotificationOutboxItem(
            id=item.id,
            event_id=item.event_id,
            email=item.email,
            access_secret=item.access_secret,
            source_filename=item.source_filename,
            status="pending",
            attempts=item.attempts + 1,
            last_error=error_message,
            created_at=item.created_at,
            sent_at=item.sent_at,
        )
        self.items[notification_id] = item
        return item


class FakeSender:
    def __init__(self, should_fail: bool):
        self.should_fail = should_fail
        self.calls = []

    def send(self, *, recipient: str, subject: str, body: str) -> None:
        self.calls.append((recipient, subject, body))
        if self.should_fail:
            raise RuntimeError("smtp unavailable")


def test_notification_use_case_sends_email_and_marks_sent():
    repo = FakeNotificationRepo()
    sender = FakeSender(should_fail=False)
    use_case = ProcessNotificationItemUseCase(notification_repository=repo, sender=sender)

    result = use_case.execute("ntf-1")
    assert result.status == "sent"
    assert sender.calls
    recipient, subject, body = sender.calls[0]
    assert recipient == "user@example.com"
    assert "Файл принят к обработке" in subject
    assert "event_id: evt-1" in body


def test_notification_use_case_marks_retry_on_sender_error():
    repo = FakeNotificationRepo()
    sender = FakeSender(should_fail=True)
    use_case = ProcessNotificationItemUseCase(notification_repository=repo, sender=sender)

    result = use_case.execute("ntf-1")
    assert result.status == "pending"
    assert result.attempts == 1
    assert "smtp unavailable" in (result.last_error or "")
