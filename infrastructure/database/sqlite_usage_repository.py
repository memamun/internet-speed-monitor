"""SQLite implementation of UsageRepository — Infrastructure layer."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import List, Optional

from domain.entities.network_usage import DailyUsage, MonthlyUsage
from domain.interfaces.usage_repository import UsageRepository

_DB_NAME = "usage_history.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS daily_usage (
    day           TEXT PRIMARY KEY,
    bytes_sent    INTEGER NOT NULL DEFAULT 0,
    bytes_recv    INTEGER NOT NULL DEFAULT 0,
    max_up_speed  INTEGER NOT NULL DEFAULT 0,
    max_down_speed INTEGER NOT NULL DEFAULT 0,
    active_seconds INTEGER NOT NULL DEFAULT 0
);
"""


class SqliteUsageRepository(UsageRepository):
    """Persists daily network usage to a local SQLite file."""

    def __init__(self, db_dir: Path | None = None) -> None:
        db_path = (db_dir or Path.cwd()) / _DB_NAME
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    # --- writes ---

    def upsert_daily(self, usage: DailyUsage) -> None:
        self._conn.execute(
            """
            INSERT INTO daily_usage (day, bytes_sent, bytes_recv,
                                     max_up_speed, max_down_speed, active_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(day) DO UPDATE SET
                bytes_sent     = excluded.bytes_sent,
                bytes_recv     = excluded.bytes_recv,
                max_up_speed   = MAX(daily_usage.max_up_speed, excluded.max_up_speed),
                max_down_speed = MAX(daily_usage.max_down_speed, excluded.max_down_speed),
                active_seconds = excluded.active_seconds
            """,
            (
                usage.day.isoformat(),
                usage.bytes_sent,
                usage.bytes_recv,
                usage.max_up_speed,
                usage.max_down_speed,
                usage.active_seconds,
            ),
        )
        self._conn.commit()

    # --- reads ---

    def get_daily(self, day: date) -> Optional[DailyUsage]:
        row = self._conn.execute(
            "SELECT * FROM daily_usage WHERE day = ?", (day.isoformat(),)
        ).fetchone()
        return self._row_to_entity(row) if row else None

    def get_range(self, start: date, end: date) -> List[DailyUsage]:
        rows = self._conn.execute(
            "SELECT * FROM daily_usage WHERE day BETWEEN ? AND ? ORDER BY day",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def get_monthly(self, year: int, month: int) -> MonthlyUsage:
        prefix = f"{year:04d}-{month:02d}"
        rows = self._conn.execute(
            "SELECT * FROM daily_usage WHERE day LIKE ?", (f"{prefix}%",)
        ).fetchall()
        mu = MonthlyUsage(year=year, month=month)
        for r in rows:
            d = self._row_to_entity(r)
            mu.bytes_sent += d.bytes_sent
            mu.bytes_recv += d.bytes_recv
            mu.max_up_speed = max(mu.max_up_speed, d.max_up_speed)
            mu.max_down_speed = max(mu.max_down_speed, d.max_down_speed)
            mu.active_seconds += d.active_seconds
            mu.days_tracked += 1
        return mu

    # --- helpers ---

    @staticmethod
    def _row_to_entity(row: tuple) -> DailyUsage:
        return DailyUsage(
            day=date.fromisoformat(row[0]),
            bytes_sent=row[1],
            bytes_recv=row[2],
            max_up_speed=row[3],
            max_down_speed=row[4],
            active_seconds=row[5],
        )

    def close(self) -> None:
        self._conn.close()
