import json
from pathlib import Path

from whisper_chunk_api.infrastructure.sqlite_tasks import SqliteWhisperTaskRepository


def test_claim_ready_marks_items_processing_without_duplicates(tmp_path: Path):
    db_path = tmp_path / "whisper.db"
    repo = SqliteWhisperTaskRepository(db_path)
    repo.ensure_schema()

    task_ids = [
        repo.create_ready(
            audio_path=f"calls/sample-{idx}.mp3",
            backend="local",
            model="tiny",
            cloud_model="whisper-1",
            task="transcribe",
            chunk_seconds=300,
            language=None,
            prompt=None,
            temperature=0.0,
        )
        for idx in range(3)
    ]

    first_batch = repo.claim_ready(limit=2)
    second_batch = repo.claim_ready(limit=2)

    assert len(first_batch) == 2
    assert len(second_batch) == 1
    assert {item.id for item in first_batch}.isdisjoint({item.id for item in second_batch})
    assert sorted(task_ids) == sorted([item.id for item in first_batch + second_batch])
    assert all(item.status == "processing" for item in first_batch + second_batch)


def test_mark_done_persists_transcript_fields(tmp_path: Path):
    db_path = tmp_path / "whisper.db"
    repo = SqliteWhisperTaskRepository(db_path)
    repo.ensure_schema()

    task_id = repo.create_ready(
        audio_path="calls/sample.mp3",
        backend="cloud",
        model="tiny",
        cloud_model="whisper-1",
        task="transcribe",
        chunk_seconds=120,
        language="ru",
        prompt="speaker names",
        temperature=0.2,
    )
    repo.claim_ready(limit=1)
    repo.mark_done(
        task_id,
        transcript_text="hello world",
        transcript_json='{"text":"hello world","chunks":[]}',
    )

    saved = repo.get(task_id)
    assert saved is not None
    assert saved.status == "done"
    assert saved.transcript_text == "hello world"
    assert json.loads(saved.transcript_json or "{}")["text"] == "hello world"
