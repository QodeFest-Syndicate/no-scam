from __future__ import annotations

import hashlib
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPLY_WINDOW = 24 * 60 * 60 - 5 * 60
RETENTION = 8 * 24 * 60 * 60
LEASE_SECONDS = 120
MAX_ATTEMPTS = 5
MAX_ACTIVE = 500
MAX_PER_SENDER = 20


class QueueFull(Exception):
    pass


@dataclass(frozen=True, repr=False)
class IncomingMessage:
    message_id: str
    sender: str
    text: str | None
    kind: str
    message_at: float


@dataclass(frozen=True, repr=False)
class Job:
    key: str
    lease: str
    message_id: str
    sender: str
    text: str | None
    kind: str
    message_at: float
    attempts: int
    reply: str | None


class WhatsAppStore:
    def __init__(self, path: Path, scope: str):
        self.path = path
        self.scope = scope

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=0.5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA secure_delete=ON")
            connection.execute("PRAGMA synchronous=FULL")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise ValueError("Unsupported WhatsApp database schema")
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS identity (id INTEGER PRIMARY KEY, scope TEXT NOT NULL)")
            db.execute("INSERT OR IGNORE INTO identity VALUES (1, ?)", (self.scope,))
            if db.execute("SELECT scope FROM identity WHERE id=1").fetchone()[0] != self.scope:
                raise ValueError("WhatsApp database belongs to another account/phone")
            db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    key TEXT PRIMARY KEY, message_id TEXT, sender TEXT, text TEXT,
                    kind TEXT NOT NULL, message_at REAL NOT NULL, received_at REAL NOT NULL,
                    state TEXT NOT NULL, available_at REAL NOT NULL, lease_until REAL NOT NULL DEFAULT 0,
                    lease TEXT, attempts INTEGER NOT NULL DEFAULT 0, reply TEXT, reason TEXT
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS jobs_ready ON jobs(state, available_at)")
            db.execute("PRAGMA user_version=1")

    def _key(self, message_id: str) -> str:
        return hashlib.sha256(f"{self.scope}:{message_id}".encode()).hexdigest()

    def enqueue(self, messages: list[IncomingMessage], now: float) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for message in messages:
                key = self._key(message.message_id)
                if db.execute("SELECT 1 FROM jobs WHERE key=?", (key,)).fetchone():
                    continue
                total = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE state IN ('pending', 'processing', 'sending')"
                ).fetchone()[0]
                per_sender = db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE sender=? AND state IN ('pending', 'processing', 'sending')",
                    (message.sender,),
                ).fetchone()[0]
                if total >= MAX_ACTIVE or per_sender >= MAX_PER_SENDER:
                    raise QueueFull()
                db.execute(
                    """INSERT INTO jobs
                       (key, message_id, sender, text, kind, message_at, received_at, state, available_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (key, message.message_id, message.sender, message.text, message.kind,
                     message.message_at, now, now),
                )

    def claim(self, now: float) -> Job | None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE jobs SET state='uncertain', reason='send_interrupted',
                   message_id=NULL, sender=NULL, text=NULL, reply=NULL, lease=NULL
                   WHERE state='sending' AND lease_until<=?""", (now,),
            )
            db.execute(
                """UPDATE jobs SET state='expired', reason='window_closed',
                   message_id=NULL, sender=NULL, text=NULL, reply=NULL, lease=NULL
                   WHERE state IN ('pending', 'processing') AND message_at+?<=?""",
                (REPLY_WINDOW, now),
            )
            db.execute(
                "UPDATE jobs SET state='pending', lease=NULL WHERE state='processing' AND lease_until<=?",
                (now,),
            )
            db.execute(
                """UPDATE jobs SET state='failed', reason='attempts_exhausted',
                   message_id=NULL, sender=NULL, text=NULL, reply=NULL, lease=NULL
                   WHERE state='pending' AND attempts>=?""", (MAX_ATTEMPTS,),
            )
            db.execute("DELETE FROM jobs WHERE received_at+?<=?", (RETENTION, now))
            row = db.execute(
                "SELECT * FROM jobs WHERE state='pending' AND available_at<=? ORDER BY received_at, rowid LIMIT 1",
                (now,),
            ).fetchone()
            if row is None:
                return None
            lease = uuid.uuid4().hex
            db.execute(
                "UPDATE jobs SET state='processing', lease=?, lease_until=?, attempts=attempts+1 WHERE key=?",
                (lease, now + LEASE_SECONDS, row["key"]),
            )
            return Job(
                key=row["key"], lease=lease, message_id=row["message_id"], sender=row["sender"],
                text=row["text"], kind=row["kind"], message_at=row["message_at"],
                attempts=row["attempts"] + 1, reply=row["reply"],
            )

    def prepare_send(self, job: Job, reply: str, now: float) -> bool:
        with self._connect() as db:
            result = db.execute(
                """UPDATE jobs SET state='sending', reply=?, text=NULL, lease_until=?
                   WHERE key=? AND lease=? AND state='processing' AND lease_until>?
                   AND message_at+?>?""",
                (reply, now + LEASE_SECONDS, job.key, job.lease, now, REPLY_WINDOW, now),
            )
            return result.rowcount == 1

    def finish(self, job: Job, state: str, reason: str) -> None:
        if state not in {"sent", "failed", "uncertain", "expired"}:
            raise ValueError("Invalid terminal state")
        with self._connect() as db:
            db.execute(
                """UPDATE jobs SET state=?, reason=?, message_id=NULL, sender=NULL, text=NULL,
                   reply=NULL, lease=NULL WHERE key=? AND lease=? AND state IN ('processing', 'sending')""",
                (state, reason, job.key, job.lease),
            )

    def retry(self, job: Job, available_at: float, reason: str) -> None:
        if job.attempts >= MAX_ATTEMPTS:
            self.finish(job, "failed", "attempts_exhausted")
        elif available_at >= job.message_at + REPLY_WINDOW:
            self.finish(job, "expired", "window_closed")
        else:
            with self._connect() as db:
                db.execute(
                    """UPDATE jobs SET state='pending', reason=?, available_at=?, lease=NULL
                       WHERE key=? AND lease=? AND state IN ('processing', 'sending')""",
                    (reason, available_at, job.key, job.lease),
                )
