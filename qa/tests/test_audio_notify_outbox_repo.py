from pathlib import Path

from audio_ingest_api.infrastructure.sqlite_outbox import SqliteNotificationOutboxRepository


def test_notification_outbox_insert_and_status_transitions(tmp_path: Path):
    db_path = tmp_path / "outbox.db"
    repo = SqliteNotificationOutboxRepository(db_path=db_path)
    repo.ensure_schema()

    notification_id = repo.create_pending_notification(
        event_id="evt-1",
        email="user@example.com",
        access_secret="sec-123",
        source_filename="sample.mp4",
    )

    pending = repo.get(notification_id)
    assert pending is not None
    assert pending.status == "pending"
    assert pending.attempts == 0

    sending = repo.mark_sending(notification_id)
    assert sending.status == "sending"

    retrying = repo.mark_retry(notification_id, "smtp timeout")
    assert retrying.status == "pending"
    assert retrying.attempts == 1
    assert retrying.last_error == "smtp timeout"

    sent = repo.mark_sent(notification_id)
    assert sent.status == "sent"
    assert sent.sent_at is not None
