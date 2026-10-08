from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from threading import Lock

from .domain import Limits, normalize_email, validate_limits


class AlertStorage:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = Lock()
        self._init_db()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self._db_path, timeout=5)
        try:
            yield connection
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recipients (
                    email TEXT NOT NULL,
                    email_key TEXT PRIMARY KEY
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS limits (
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    temp_max REAL NOT NULL,
                    humi_min REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO limits(id, temp_max, humi_min)
                SELECT 1, 35.0, 20.0
                WHERE NOT EXISTS (SELECT 1 FROM limits WHERE id=1)
                """
            )
            conn.commit()

    def list_emails(self) -> list[str]:
        with self._connection() as conn:
            rows = conn.execute("SELECT email FROM recipients ORDER BY email_key").fetchall()
        return [row[0] for row in rows]

    def add_email(self, email: str) -> list[str]:
        clean_email, email_key = normalize_email(email)
        with self._lock, self._connection() as conn:
            existing = conn.execute(
                "SELECT 1 FROM recipients WHERE email_key = ?", (email_key,)
            ).fetchone()
            if existing:
                raise ValueError("Email already registered")
            conn.execute(
                "INSERT INTO recipients(email, email_key) VALUES (?, ?)", (clean_email, email_key)
            )
            conn.commit()
        return self.list_emails()

    def remove_email(self, email: str) -> list[str]:
        clean_email, email_key = normalize_email(email)
        _ = clean_email
        with self._lock, self._connection() as conn:
            conn.execute("DELETE FROM recipients WHERE email_key = ?", (email_key,))
            conn.commit()
        return self.list_emails()

    def get_limits(self) -> Limits:
        with self._connection() as conn:
            row = conn.execute("SELECT temp_max, humi_min FROM limits WHERE id = 1").fetchone()
        if row is None:
            raise RuntimeError("Limits configuration missing")
        return Limits(temp_max=float(row[0]), humi_min=float(row[1]))

    def update_limits(self, temp: object, humi: object) -> Limits:
        limits = validate_limits(temp=temp, humi=humi)
        with self._lock, self._connection() as conn:
            conn.execute(
                "UPDATE limits SET temp_max = ?, humi_min = ? WHERE id = 1",
                (limits.temp_max, limits.humi_min),
            )
            conn.commit()
        return limits
