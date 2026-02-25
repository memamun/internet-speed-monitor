"""Wraps psutil network I/O — Infrastructure layer."""

from __future__ import annotations

import psutil

from domain.entities.network_usage import SpeedSnapshot


class NetworkProvider:
    """Reads raw network byte counters from the OS."""

    def __init__(self) -> None:
        counters = psutil.net_io_counters()
        self._last_sent: int = counters.bytes_sent
        self._last_recv: int = counters.bytes_recv

    def snapshot(self) -> SpeedSnapshot:
        """Return the delta since the last call (call once per second)."""
        counters = psutil.net_io_counters()
        sent_delta = counters.bytes_sent - self._last_sent
        recv_delta = counters.bytes_recv - self._last_recv
        self._last_sent = counters.bytes_sent
        self._last_recv = counters.bytes_recv
        return SpeedSnapshot(
            up_speed=max(sent_delta, 0),
            down_speed=max(recv_delta, 0),
            bytes_sent_delta=max(sent_delta, 0),
            bytes_recv_delta=max(recv_delta, 0),
        )
