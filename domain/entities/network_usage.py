"""Domain entities for SpeedMonitor — pure Python, no external dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class DailyUsage:
    """Represents one day's accumulated network usage."""

    day: date
    bytes_sent: int = 0
    bytes_recv: int = 0
    max_up_speed: int = 0   # B/s
    max_down_speed: int = 0  # B/s
    active_seconds: int = 0  # seconds the monitor was running

    # --- derived properties ---

    @property
    def total_bytes(self) -> int:
        return self.bytes_sent + self.bytes_recv

    @property
    def avg_up_speed(self) -> float:
        """Average upload speed in B/s over active time."""
        return self.bytes_sent / self.active_seconds if self.active_seconds else 0.0

    @property
    def avg_down_speed(self) -> float:
        """Average download speed in B/s over active time."""
        return self.bytes_recv / self.active_seconds if self.active_seconds else 0.0

    @property
    def avg_total_speed(self) -> float:
        return self.avg_up_speed + self.avg_down_speed


@dataclass
class MonthlyUsage:
    """Aggregated usage for a calendar month."""

    year: int
    month: int
    bytes_sent: int = 0
    bytes_recv: int = 0
    max_up_speed: int = 0
    max_down_speed: int = 0
    active_seconds: int = 0
    days_tracked: int = 0

    @property
    def total_bytes(self) -> int:
        return self.bytes_sent + self.bytes_recv

    @property
    def avg_up_speed(self) -> float:
        return self.bytes_sent / self.active_seconds if self.active_seconds else 0.0

    @property
    def avg_down_speed(self) -> float:
        return self.bytes_recv / self.active_seconds if self.active_seconds else 0.0


@dataclass
class SpeedSnapshot:
    """A single point-in-time speed reading (not persisted, used in-memory)."""

    up_speed: int = 0   # B/s
    down_speed: int = 0  # B/s
    bytes_sent_delta: int = 0
    bytes_recv_delta: int = 0
