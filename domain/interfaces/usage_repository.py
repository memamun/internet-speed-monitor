"""Abstract interface for usage data persistence — Domain layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from domain.entities.network_usage import DailyUsage, MonthlyUsage


class UsageRepository(ABC):
    """Contract that any storage backend must implement."""

    @abstractmethod
    def upsert_daily(self, usage: DailyUsage) -> None:
        """Insert or update a single day's usage record."""

    @abstractmethod
    def get_daily(self, day: date) -> Optional[DailyUsage]:
        """Retrieve usage for a specific day, or None."""

    @abstractmethod
    def get_range(self, start: date, end: date) -> List[DailyUsage]:
        """Retrieve all daily records within [start, end] inclusive."""

    @abstractmethod
    def get_monthly(self, year: int, month: int) -> MonthlyUsage:
        """Aggregate usage for a given calendar month."""
