"""Statistics Window — Presentation layer.

Displays daily, monthly, and custom-range network usage statistics
in a dark-themed Tkinter window, matching the SpeedMonitor aesthetic.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.interfaces.usage_repository import UsageRepository


def _fmt_bytes(b: int) -> str:
    """Human-readable byte count."""
    if b >= 1024 ** 3:
        return f"{b / 1024**3:.2f} GB"
    if b >= 1024 ** 2:
        return f"{b / 1024**2:.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b} B"


def _fmt_speed(bps: float) -> str:
    if bps >= 1024 ** 3:
        return f"{bps / 1024**3:.2f} GB/s"
    if bps >= 1024 ** 2:
        return f"{bps / 1024**2:.2f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.2f} KB/s"
    return f"{bps:.0f} B/s"


# ── Colors ───────────────────────────────────────────────────────────────────

BG = "#1e1e1e"
FG = "#ffffff"
ACCENT = "#00e5ff"
SECTION_BG = "#2a2a2a"
HEADER_FG = "#f39c12"
MUTED = "#888888"
FONT = ("Segoe UI Semibold", 10)
FONT_SM = ("Segoe UI", 9)
FONT_LG = ("Segoe UI Semibold", 14)


class StatisticsWindow:
    """Standalone Toplevel window showing usage data."""

    def __init__(self, parent: tk.Tk, repo: "UsageRepository") -> None:
        self._repo = repo
        self._win = tk.Toplevel(parent)
        self._win.title("SpeedMonitor — Usage Statistics")
        self._win.configure(bg=BG)
        self._win.geometry("420x520")
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)

        self._build_ui()
        self._refresh()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Title
        tk.Label(self._win, text="SpeedMonitor", font=FONT_LG, fg=ACCENT,
                 bg=BG).pack(pady=(12, 4))
        tk.Label(self._win, text="Network Usage Statistics", font=FONT_SM,
                 fg=MUTED, bg=BG).pack()

        # Today section
        self._today_frame = self._section("Today")
        self._lbl_today_up = self._row(self._today_frame, "↑ Upload")
        self._lbl_today_dn = self._row(self._today_frame, "↓ Download")
        self._lbl_today_total = self._row(self._today_frame, "Total")
        self._lbl_today_max_up = self._row(self._today_frame, "Peak ↑ Speed")
        self._lbl_today_max_dn = self._row(self._today_frame, "Peak ↓ Speed")
        self._lbl_today_avg = self._row(self._today_frame, "Avg Speed")

        # This month section
        self._month_frame = self._section("This Month")
        self._lbl_month_up = self._row(self._month_frame, "↑ Upload")
        self._lbl_month_dn = self._row(self._month_frame, "↓ Download")
        self._lbl_month_total = self._row(self._month_frame, "Total")
        self._lbl_month_peak_up = self._row(self._month_frame, "Peak ↑ Speed")
        self._lbl_month_peak_dn = self._row(self._month_frame, "Peak ↓ Speed")
        self._lbl_month_days = self._row(self._month_frame, "Days Tracked")

        # Buttons
        btn_frame = tk.Frame(self._win, bg=BG)
        btn_frame.pack(fill=tk.X, padx=16, pady=(8, 12))
        tk.Button(btn_frame, text="↻ Refresh", font=FONT_SM, bg="#333",
                  fg=FG, activebackground="#555", activeforeground=FG,
                  relief="flat", bd=0, padx=12, pady=4,
                  command=self._refresh).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Close", font=FONT_SM, bg="#333",
                  fg=FG, activebackground="#555", activeforeground=FG,
                  relief="flat", bd=0, padx=12, pady=4,
                  command=self._win.destroy).pack(side=tk.RIGHT)

    def _section(self, title: str) -> tk.Frame:
        tk.Label(self._win, text=title, font=FONT, fg=HEADER_FG,
                 bg=BG, anchor="w").pack(fill=tk.X, padx=16, pady=(12, 2))
        frame = tk.Frame(self._win, bg=SECTION_BG, bd=0, highlightthickness=0)
        frame.pack(fill=tk.X, padx=16, pady=(0, 4))
        return frame

    def _row(self, parent: tk.Frame, label: str) -> tk.Label:
        row = tk.Frame(parent, bg=SECTION_BG)
        row.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(row, text=label, font=FONT_SM, fg=MUTED, bg=SECTION_BG,
                 anchor="w").pack(side=tk.LEFT)
        val = tk.Label(row, text="—", font=FONT_SM, fg=FG, bg=SECTION_BG,
                       anchor="e")
        val.pack(side=tk.RIGHT)
        return val

    # ── Data refresh ─────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        today = date.today()

        # Today
        d = self._repo.get_daily(today)
        if d:
            self._lbl_today_up.config(text=_fmt_bytes(d.bytes_sent))
            self._lbl_today_dn.config(text=_fmt_bytes(d.bytes_recv))
            self._lbl_today_total.config(text=_fmt_bytes(d.total_bytes))
            self._lbl_today_max_up.config(text=_fmt_speed(d.max_up_speed))
            self._lbl_today_max_dn.config(text=_fmt_speed(d.max_down_speed))
            self._lbl_today_avg.config(text=_fmt_speed(d.avg_total_speed))
        else:
            for lbl in (self._lbl_today_up, self._lbl_today_dn,
                        self._lbl_today_total, self._lbl_today_max_up,
                        self._lbl_today_max_dn, self._lbl_today_avg):
                lbl.config(text="—")

        # This month
        m = self._repo.get_monthly(today.year, today.month)
        self._lbl_month_up.config(text=_fmt_bytes(m.bytes_sent))
        self._lbl_month_dn.config(text=_fmt_bytes(m.bytes_recv))
        self._lbl_month_total.config(text=_fmt_bytes(m.total_bytes))
        self._lbl_month_peak_up.config(text=_fmt_speed(m.max_up_speed))
        self._lbl_month_peak_dn.config(text=_fmt_speed(m.max_down_speed))
        self._lbl_month_days.config(text=str(m.days_tracked))
