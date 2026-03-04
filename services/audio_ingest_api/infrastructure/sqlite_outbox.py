import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from audio_ingest_api.application.dto import NotificationOutboxItem, OutboxItem
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
                    created_at TEXT NOT NULL,
                    access_secret_hash TEXT NOT NULL
                )
                """
            )
            columns = conn.execute("PRAGMA table_info(outbox)").fetchall()
            column_names = {row["name"] for row in columns}
            if "access_secret_hash" not in column_names:
                conn.execute("ALTER TABLE outbox ADD COLUMN access_secret_hash TEXT NOT NULL DEFAULT ''")
            conn.commit()

    def create_pending(
        self, email: str, source_filename: str, source_path: str, access_secret_hash: str
    ) -> str:
        event_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO outbox (
                    id,
                    email,
                    source_filename,
                    source_path,
                    audio_path,
                    status,
                    created_at,
                    access_secret_hash
                )
                VALUES (?, ?, ?, ?, NULL, 'pending', ?, ?)
                """,
                (event_id, email, source_filename, source_path, created_at, access_secret_hash),
            )
            conn.commit()
        return event_id

    def list_pending(self, limit: int) -> list[OutboxItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, email, source_filename, source_path, audio_path, status, created_at, access_secret_hash
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
                SELECT id, email, source_filename, source_path, audio_path, status, created_at, access_secret_hash
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
            access_secret_hash=row["access_secret_hash"],
        )


class SqliteNotificationOutboxRepository:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_outbox (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    access_secret TEXT NOT NULL,
                    source_filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    sent_at TEXT
                )
                """
            )
            conn.commit()

    def create_pending_notification(
        self,
        *,
        event_id: str,
        email: str,
        access_secret: str,
        source_filename: str,
    ) -> str:
        notification_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO notification_outbox (
                    id, event_id, email, access_secret, source_filename, status, attempts, last_error, created_at, sent_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', 0, NULL, ?, NULL)
                """,
                (notification_id, event_id, email, access_secret, source_filename, created_at),
            )
            conn.commit()
        return notification_id

    def list_pending(self, limit: int) -> list[NotificationOutboxItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, event_id, email, access_secret, source_filename, status, attempts, last_error, created_at, sent_at
                FROM notification_outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def mark_sending(self, notification_id: str) -> NotificationOutboxItem:
        with self._connect() as conn:
            conn.execute(
                "UPDATE notification_outbox SET status = 'sending' WHERE id = ?",
                (notification_id,),
            )
            conn.commit()
        return self._require(notification_id)

    def mark_sent(self, notification_id: str) -> NotificationOutboxItem:
        sent_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "UPDATE notification_outbox SET status = 'sent', sent_at = ?, last_error = NULL WHERE id = ?",
                (sent_at, notification_id),
            )
            conn.commit()
        return self._require(notification_id)

    def mark_retry(self, notification_id: str, error_message: str) -> NotificationOutboxItem:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE notification_outbox
                SET status = 'pending',
                    attempts = attempts + 1,
                    last_error = ?
                WHERE id = ?
                """,
                (error_message[:1024], notification_id),
            )
            conn.commit()
        return self._require(notification_id)

    def get(self, notification_id: str) -> NotificationOutboxItem | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, event_id, email, access_secret, source_filename, status, attempts, last_error, created_at, sent_at
                FROM notification_outbox
                WHERE id = ?
                """,
                (notification_id,),
            ).fetchone()
        return self._row_to_item(row) if row else None

    def diagnostics(self) -> dict[str, int]:
        with self._connect() as conn:
            total = int(conn.execute("SELECT COUNT(1) FROM notification_outbox").fetchone()[0])
            pending = int(
                conn.execute("SELECT COUNT(1) FROM notification_outbox WHERE status = 'pending'").fetchone()[0]
            )
            sending = int(
                conn.execute("SELECT COUNT(1) FROM notification_outbox WHERE status = 'sending'").fetchone()[0]
            )
            sent = int(conn.execute("SELECT COUNT(1) FROM notification_outbox WHERE status = 'sent'").fetchone()[0])
            with_errors = int(
                conn.execute(
                    "SELECT COUNT(1) FROM notification_outbox WHERE last_error IS NOT NULL AND last_error != ''"
                ).fetchone()[0]
            )
        return {
            "total": total,
            "pending": pending,
            "sending": sending,
            "sent": sent,
            "with_errors": with_errors,
        }

    def _require(self, notification_id: str) -> NotificationOutboxItem:
        item = self.get(notification_id)
        if not item:
            raise NotFoundError(f"Notification outbox item not found: {notification_id}")
        return item

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> NotificationOutboxItem:
        sent_at = datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None
        return NotificationOutboxItem(
            id=row["id"],
            event_id=row["event_id"],
            email=row["email"],
            access_secret=row["access_secret"],
            source_filename=row["source_filename"],
            status=row["status"],
            attempts=int(row["attempts"]),
            last_error=row["last_error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            sent_at=sent_at,
        )

