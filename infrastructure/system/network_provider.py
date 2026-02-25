"""Wraps psutil network I/O — Infrastructure layer."""

from __future__ import annotations

import psutil

from domain.entities.network_usage import SpeedSnapshot


from domain.entities.configuration import AppConfig


class NetworkProvider:
    """Reads raw network byte counters from the OS."""

    def __init__(self, config: AppConfig = None) -> None:
        self.config = config
        self._last_sent: int = 0
        self._last_recv: int = 0
        self._init_counters()

    def _init_counters(self) -> None:
        """Sets initial baseline so the first second doesn't show a huge spike."""
        self._last_sent, self._last_recv = self._get_current_bytes()

    def _get_current_bytes(self) -> tuple[int, int]:
        adapter = "All"
        if self.config:
            adapter = self.config.monitored_adapter

        if adapter == "All":
            counters = psutil.net_io_counters()
            return counters.bytes_sent, counters.bytes_recv
        else:
            counters = psutil.net_io_counters(pernic=True)
            if adapter in counters:
                return counters[adapter].bytes_sent, counters[adapter].bytes_recv
            else:  # Fall back to all if adapter vanishes
                counters_all = psutil.net_io_counters()
                return counters_all.bytes_sent, counters_all.bytes_recv

    def snapshot(self) -> SpeedSnapshot:
        """Return the delta since the last call (call once per second)."""
        sent, recv = self._get_current_bytes()

        sent_delta = sent - self._last_sent
        recv_delta = recv - self._last_recv

        self._last_sent = sent
        self._last_recv = recv
        return SpeedSnapshot(
            up_speed=max(sent_delta, 0),
            down_speed=max(recv_delta, 0),
            bytes_sent_delta=max(sent_delta, 0),
            bytes_recv_delta=max(recv_delta, 0),
        )
