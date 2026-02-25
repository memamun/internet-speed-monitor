"""Application service — orchestrates speed monitoring and usage tracking."""

from __future__ import annotations

import time
import threading
from datetime import date
from typing import Callable, Optional

from domain.entities.network_usage import DailyUsage, SpeedSnapshot
from domain.interfaces.usage_repository import UsageRepository
from infrastructure.system.network_provider import NetworkProvider

# How often (in seconds) to flush accumulated data to the database
_FLUSH_INTERVAL = 10


class SpeedMonitorService:
    """Coordinates network polling, in-memory accumulation, and periodic DB flush."""

    def __init__(
        self,
        network: NetworkProvider,
        repo: UsageRepository,
        on_speed_update: Optional[Callable[[SpeedSnapshot], None]] = None,
    ) -> None:
        self._net = network
        self._repo = repo
        self._on_speed_update = on_speed_update

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # In-memory accumulators (flushed periodically)
        self._today: date = date.today()
        self._bytes_sent: int = 0
        self._bytes_recv: int = 0
        self._max_up: int = 0
        self._max_down: int = 0
        self._active_secs: int = 0
        self._flush_counter: int = 0

        # Load existing today data from DB if present
        existing = self._repo.get_daily(self._today)
        if existing:
            self._bytes_sent = existing.bytes_sent
            self._bytes_recv = existing.bytes_recv
            self._max_up = existing.max_up_speed
            self._max_down = existing.max_down_speed
            self._active_secs = existing.active_seconds

    # ── public API ───────────────────────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._flush()  # final flush

    @property
    def today_usage(self) -> DailyUsage:
        return DailyUsage(
            day=self._today,
            bytes_sent=self._bytes_sent,
            bytes_recv=self._bytes_recv,
            max_up_speed=self._max_up,
            max_down_speed=self._max_down,
            active_seconds=self._active_secs,
        )

    # ── internals ────────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            try:
                snap = self._net.snapshot()
                self._accumulate(snap)
                if self._on_speed_update:
                    self._on_speed_update(snap)
            except Exception:
                pass
            time.sleep(1)

    def _accumulate(self, snap: SpeedSnapshot) -> None:
        now = date.today()
        if now != self._today:
            # Day rolled over — flush yesterday and reset
            self._flush()
            self._today = now
            self._bytes_sent = 0
            self._bytes_recv = 0
            self._max_up = 0
            self._max_down = 0
            self._active_secs = 0

        self._bytes_sent += snap.bytes_sent_delta
        self._bytes_recv += snap.bytes_recv_delta
        self._max_up = max(self._max_up, snap.up_speed)
        self._max_down = max(self._max_down, snap.down_speed)
        self._active_secs += 1

        self._flush_counter += 1
        if self._flush_counter >= _FLUSH_INTERVAL:
            self._flush()
            self._flush_counter = 0

    def _flush(self) -> None:
        try:
            self._repo.upsert_daily(self.today_usage)
        except Exception:
            pass
