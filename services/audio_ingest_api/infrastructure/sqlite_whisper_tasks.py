import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class WhisperTaskSnapshot:
    def __init__(
        self,
        *,
        task_id: str,
        status: str,
        transcript_text: str | None,
        transcript_json: str | None,
        summary: str | None,
        error: str | None,
    ):
        self.task_id = task_id
        self.status = status
        self.transcript_text = transcript_text
        self.transcript_json = transcript_json
        self.summary = summary
        self.error = error


class SqliteWhisperTaskQueue:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS whisper_tasks (
                    id TEXT PRIMARY KEY,
                    audio_path TEXT NOT NULL,
                    event_id TEXT,
                    requester_email TEXT,
                    status TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    model TEXT NOT NULL,
                    cloud_model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    chunk_seconds INTEGER NOT NULL,
                    language TEXT,
                    prompt TEXT,
                    temperature REAL NOT NULL,
                    transcript_text TEXT,
                    transcript_json TEXT,
                    summary TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                )
                """
            )
            columns = conn.execute("PRAGMA table_info(whisper_tasks)").fetchall()
            column_names = {row["name"] for row in columns}
            if "summary" not in column_names:
                conn.execute("ALTER TABLE whisper_tasks ADD COLUMN summary TEXT")
            if "event_id" not in column_names:
                conn.execute("ALTER TABLE whisper_tasks ADD COLUMN event_id TEXT")
            if "requester_email" not in column_names:
                conn.execute("ALTER TABLE whisper_tasks ADD COLUMN requester_email TEXT")
            conn.commit()

    def enqueue_ready_task(
        self,
        *,
        audio_path: str,
        event_id: str | None,
        requester_email: str | None,
        backend: str,
        model: str,
        cloud_model: str,
        task: str,
        chunk_seconds: int,
        language: str | None,
        prompt: str | None,
        temperature: float,
    ) -> str:
        task_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO whisper_tasks (
                    id, audio_path, event_id, requester_email, status, backend, model, cloud_model, task, chunk_seconds,
                    language, prompt, temperature, transcript_text, transcript_json, summary, error,
                    created_at, started_at, finished_at
                )
                VALUES (?, ?, ?, ?, 'ready', ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, ?, NULL, NULL)
                """,
                (
                    task_id,
                    audio_path,
                    event_id,
                    requester_email,
                    backend,
                    model,
                    cloud_model,
                    task,
                    chunk_seconds,
                    language,
                    prompt,
                    temperature,
                    created_at,
                ),
            )
            conn.commit()
        return task_id

    def get_latest_by_audio_path(self, audio_path: str) -> WhisperTaskSnapshot | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, status, transcript_text, transcript_json, summary, error
                FROM whisper_tasks
                WHERE audio_path = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (audio_path,),
            ).fetchone()
        if not row:
            return None
        return WhisperTaskSnapshot(
            task_id=row["id"],
            status=row["status"],
            transcript_text=row["transcript_text"],
            transcript_json=row["transcript_json"],
            summary=row["summary"],
            error=row["error"],
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
