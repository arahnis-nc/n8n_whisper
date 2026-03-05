import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from whisper_chunk_api.application.dto import WhisperTaskItem
from whisper_chunk_api.application.errors import NotFoundError


class SqliteWhisperTaskRepository:
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

    def create_ready(
        self,
        *,
        audio_path: str,
        backend: str,
        model: str,
        cloud_model: str,
        task: str,
        chunk_seconds: int,
        language: str | None,
        prompt: str | None,
        temperature: float,
        event_id: str | None = None,
        requester_email: str | None = None,
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

    def claim_ready(self, limit: int) -> list[WhisperTaskItem]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """
                SELECT id
                FROM whisper_tasks
                WHERE status = 'ready'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            if not rows:
                conn.commit()
                return []
            task_ids = [row["id"] for row in rows]
            conn.executemany(
                "UPDATE whisper_tasks SET status = 'processing', started_at = ? WHERE id = ?",
                [(now, task_id) for task_id in task_ids],
            )
            conn.commit()
        return [self._require(task_id) for task_id in task_ids]

    def mark_done(self, task_id: str, *, transcript_text: str, transcript_json: str, summary: str | None) -> WhisperTaskItem:
        finished_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE whisper_tasks
                SET status = 'done',
                    transcript_text = ?,
                    transcript_json = ?,
                    summary = ?,
                    error = NULL,
                    finished_at = ?
                WHERE id = ?
                """,
                (transcript_text, transcript_json, summary, finished_at, task_id),
            )
            conn.commit()
        return self._require(task_id)

    def mark_failed(self, task_id: str, *, error_message: str) -> WhisperTaskItem:
        finished_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE whisper_tasks
                SET status = 'failed',
                    error = ?,
                    finished_at = ?
                WHERE id = ?
                """,
                (error_message[:1024], finished_at, task_id),
            )
            conn.commit()
        return self._require(task_id)

    def get(self, task_id: str) -> WhisperTaskItem | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, audio_path, status, backend, model, cloud_model, task, chunk_seconds,
                       event_id, requester_email, language, prompt, temperature, transcript_text, transcript_json, summary, error
                FROM whisper_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return self._row_to_item(row) if row else None

    def _require(self, task_id: str) -> WhisperTaskItem:
        item = self.get(task_id)
        if not item:
            raise NotFoundError(f"Whisper task not found: {task_id}")
        return item

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> WhisperTaskItem:
        return WhisperTaskItem(
            id=row["id"],
            audio_path=row["audio_path"],
            event_id=row["event_id"],
            requester_email=row["requester_email"],
            status=row["status"],
            backend=row["backend"],
            model=row["model"],
            cloud_model=row["cloud_model"],
            task=row["task"],
            chunk_seconds=int(row["chunk_seconds"]),
            language=row["language"],
            prompt=row["prompt"],
            temperature=float(row["temperature"]),
            transcript_text=row["transcript_text"],
            transcript_json=row["transcript_json"],
            summary=row["summary"],
            error=row["error"],
        )
