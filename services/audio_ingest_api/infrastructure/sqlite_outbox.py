import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from audio_ingest_api.application.dto import OutboxItem
from audio_ingest_api.application.errors import NotFoundError


class SqliteOutboxRepository:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    source_filename TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    audio_path TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_pending(self, email: str, source_filename: str, source_path: str) -> str:
        event_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO outbox (id, email, source_filename, source_path, audio_path, status, created_at)
                VALUES (?, ?, ?, ?, NULL, 'pending', ?)
                """,
                (event_id, email, source_filename, source_path, created_at),
            )
            conn.commit()
        return event_id

    def list_pending(self, limit: int) -> list[OutboxItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, email, source_filename, source_path, audio_path, status, created_at
                FROM outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def mark_processing(self, event_id: str) -> OutboxItem:
        with self._connect() as conn:
            conn.execute(
                "UPDATE outbox SET status = 'processing' WHERE id = ?",
                (event_id,),
            )
            conn.commit()
        return self._require(event_id)

    def mark_ready(self, event_id: str, audio_path: str) -> OutboxItem:
        with self._connect() as conn:
            conn.execute(
                "UPDATE outbox SET status = 'ready', audio_path = ? WHERE id = ?",
                (audio_path, event_id),
            )
            conn.commit()
        return self._require(event_id)

    def mark_failed(self, event_id: str) -> OutboxItem:
        with self._connect() as conn:
            conn.execute(
                "UPDATE outbox SET status = 'failed' WHERE id = ?",
                (event_id,),
            )
            conn.commit()
        return self._require(event_id)

    def get(self, event_id: str) -> OutboxItem | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, email, source_filename, source_path, audio_path, status, created_at
                FROM outbox
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()
        return self._row_to_item(row) if row else None

    def _require(self, event_id: str) -> OutboxItem:
        item = self.get(event_id)
        if not item:
            raise NotFoundError(f"Outbox event not found: {event_id}")
        return item

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> OutboxItem:
        return OutboxItem(
            id=row["id"],
            email=row["email"],
            source_filename=row["source_filename"],
            source_path=row["source_path"],
            audio_path=row["audio_path"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

