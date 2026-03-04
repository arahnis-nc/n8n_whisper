from pathlib import Path

from audio_ingest_api.infrastructure.sqlite_outbox import SqliteOutboxRepository


def test_outbox_insert_and_transition(tmp_path: Path):
    db_path = tmp_path / "outbox.db"
    repo = SqliteOutboxRepository(db_path=db_path)
    repo.ensure_schema()

    event_id = repo.create_pending(
        email="user@example.com",
        source_filename="sample.mp4",
        source_path=str(tmp_path / "inbox" / "sample.mp4"),
        access_secret_hash="hash-value",
    )

    pending = repo.get(event_id)
    assert pending is not None
    assert pending.status == "pending"
    assert pending.access_secret_hash == "hash-value"

    processing = repo.mark_processing(event_id)
    assert processing.status == "processing"

    ready = repo.mark_ready(event_id, audio_path=str(tmp_path / "processed" / "sample.wav"))
    assert ready.status == "ready"
    assert ready.audio_path is not None
    assert ready.audio_path.endswith(".wav")

