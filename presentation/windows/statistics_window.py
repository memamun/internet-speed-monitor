"""Statistics Window — Presentation layer.

Premium dark-themed window displaying daily, monthly, and custom-range
network usage statistics for SpeedMonitor.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.interfaces.usage_repository import UsageRepository

# ── Palette ──────────────────────────────────────────────────────────────────

BG          = "#0f0f0f"
BG_SURFACE  = "#1a1a1a"
BG_CARD     = "#222222"
BG_CARD2    = "#1d1d1d"
BORDER      = "#2e2e2e"
FG          = "#f0f0f0"
FG_DIM      = "#888888"
ACCENT_UP   = "#f39c12"   # orange — upload
ACCENT_DN   = "#00e5ff"   # cyan   — download
ACCENT_MAIN = "#7c6af7"   # purple — primary accent
GREEN       = "#27ae60"
SEPARATOR   = "#2a2a2a"

# ── Fonts ─────────────────────────────────────────────────────────────────────

def _f(size: int, weight: str = "normal") -> tuple:
    return ("Segoe UI", size, weight)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_bytes(b: int) -> str:
    if b >= 1024 ** 3: return f"{b / 1024**3:.2f} GB"
    if b >= 1024 ** 2: return f"{b / 1024**2:.2f} MB"
    if b >= 1024:      return f"{b / 1024:.2f} KB"
    return f"{b} B"


def _fmt_speed(bps: float) -> str:
    if bps >= 1024 ** 3: return f"{bps / 1024**3:.2f} GB/s"
    if bps >= 1024 ** 2: return f"{bps / 1024**2:.2f} MB/s"
    if bps >= 1024:      return f"{bps / 1024:.2f} KB/s"
    return f"{bps:.0f} B/s"


# ── Main Window ───────────────────────────────────────────────────────────────

class StatisticsWindow:
    """Premium statistics popup window."""

    WIDTH  = 460
    HEIGHT = 600

    def __init__(self, parent: tk.Tk, repo: "UsageRepository") -> None:
        self._repo = repo
        self._win = tk.Toplevel(parent)
        self._win.title("SpeedMonitor — Statistics")
        self._win.configure(bg=BG)
        self._win.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)

        # Center on screen
        self._win.update_idletasks()
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = (sh - self.HEIGHT) // 2
        self._win.geometry(f"+{x}+{y}")

        self._build()
        self._refresh()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Header bar ──────────────────────────────────────────────────────
        header = tk.Frame(self._win, bg=BG_SURFACE, height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Left: icon + title
        left = tk.Frame(header, bg=BG_SURFACE)
        left.pack(side=tk.LEFT, padx=20, pady=12)
        canvas = tk.Canvas(left, width=28, height=28, bg=BG_SURFACE,
                           highlightthickness=0)
        canvas.pack(side=tk.LEFT, padx=(0, 10))
        # Draw small arrow icon
        canvas.create_polygon(14, 2, 5, 14, 12, 14, fill=ACCENT_UP, outline="")
        canvas.create_polygon(14, 26, 23, 14, 16, 14, fill=ACCENT_DN, outline="")

        tk.Label(left, text="SpeedMonitor", font=_f(13, "bold"),
                 fg=FG, bg=BG_SURFACE).pack(side=tk.LEFT)

        # Right: date
        tk.Label(header, text=date.today().strftime("%B %d, %Y"),
                 font=_f(9), fg=FG_DIM, bg=BG_SURFACE).pack(
            side=tk.RIGHT, padx=20)

        # ── Tab bar ─────────────────────────────────────────────────────────
        self._tab_var = tk.StringVar(value="today")
        tab_bar = tk.Frame(self._win, bg=BG, pady=0)
        tab_bar.pack(fill=tk.X, padx=20, pady=(14, 0))

        self._tabs: dict[str, tk.Label] = {}
        for key, text in (("today", "Today"), ("month", "This Month")):
            lbl = tk.Label(tab_bar, text=text, font=_f(10),
                           bg=BG, fg=FG_DIM, cursor="hand2", padx=12, pady=6)
            lbl.pack(side=tk.LEFT)
            lbl.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self._tabs[key] = lbl

        self._tab_indicator = tk.Frame(tab_bar, bg=ACCENT_MAIN, height=2)
        # (positioned dynamically in _switch_tab)

        # ── Divider ─────────────────────────────────────────────────────────
        tk.Frame(self._win, bg=BORDER, height=1).pack(fill=tk.X, padx=20, pady=(4, 0))

        # ── Content area (swappable frames) ─────────────────────────────────
        self._content = tk.Frame(self._win, bg=BG)
        self._content.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        self._today_frame  = self._build_today_frame()
        self._month_frame  = self._build_month_frame()

        # ── Footer ──────────────────────────────────────────────────────────
        footer = tk.Frame(self._win, bg=BG_SURFACE, height=52)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        _Btn(footer, "↻  Refresh", command=self._refresh).pack(
            side=tk.LEFT, padx=16, pady=10)
        _Btn(footer, "Close", primary=True, command=self._win.destroy).pack(
            side=tk.RIGHT, padx=16, pady=10)

        # Activate today tab
        self._switch_tab("today")

    def _build_today_frame(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        # Big total usage stat
        hero = _Card(f, padx=20, pady=16)
        hero.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hero, text="Total Usage Today", font=_f(9),
                 fg=FG_DIM, bg=BG_CARD).pack(anchor="w")
        self._lbl_today_total = tk.Label(hero, text="—", font=_f(24, "bold"),
                                          fg=FG, bg=BG_CARD)
        self._lbl_today_total.pack(anchor="w", pady=(4, 0))

        # Upload / Download side-by-side
        row = tk.Frame(f, bg=BG)
        row.pack(fill=tk.X, pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ul_card = _Card(row, padx=16, pady=14)
        ul_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tk.Label(ul_card, text="↑  UPLOAD", font=_f(8), fg=ACCENT_UP,
                 bg=BG_CARD).pack(anchor="w")
        self._lbl_today_up = tk.Label(ul_card, text="—", font=_f(14, "bold"),
                                       fg=FG, bg=BG_CARD)
        self._lbl_today_up.pack(anchor="w", pady=(6, 0))

        dn_card = _Card(row, padx=16, pady=14)
        dn_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tk.Label(dn_card, text="↓  DOWNLOAD", font=_f(8), fg=ACCENT_DN,
                 bg=BG_CARD).pack(anchor="w")
        self._lbl_today_dn = tk.Label(dn_card, text="—", font=_f(14, "bold"),
                                       fg=FG, bg=BG_CARD)
        self._lbl_today_dn.pack(anchor="w", pady=(6, 0))

        # Speed stats grid
        speed_card = _Card(f, padx=16, pady=14)
        speed_card.pack(fill=tk.X, pady=(0, 10))

        tk.Label(speed_card, text="SPEED METRICS", font=_f(8),
                 fg=FG_DIM, bg=BG_CARD).pack(anchor="w", pady=(0, 10))

        speed_rows = tk.Frame(speed_card, bg=BG_CARD)
        speed_rows.pack(fill=tk.X)
        speed_rows.columnconfigure(1, weight=1)

        self._lbl_today_avg    = self._stat_row(speed_rows, "Avg Speed",      0)
        self._lbl_today_max_up = self._stat_row(speed_rows, "Peak ↑ Upload",  1)
        self._lbl_today_max_dn = self._stat_row(speed_rows, "Peak ↓ Download",2)

        # Active time
        fmt_card = _Card(f, padx=16, pady=12)
        fmt_card.pack(fill=tk.X)
        tk.Label(fmt_card, text="MONITORING TIME", font=_f(8),
                 fg=FG_DIM, bg=BG_CARD).pack(anchor="w", pady=(0, 6))
        self._lbl_today_time = tk.Label(fmt_card, text="—", font=_f(11),
                                         fg=FG, bg=BG_CARD)
        self._lbl_today_time.pack(anchor="w")

        return f

    def _build_month_frame(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        hero = _Card(f, padx=20, pady=16)
        hero.pack(fill=tk.X, pady=(0, 10))
        tk.Label(hero, text=f"Total — {date.today().strftime('%B %Y')}",
                 font=_f(9), fg=FG_DIM, bg=BG_CARD).pack(anchor="w")
        self._lbl_month_total = tk.Label(hero, text="—", font=_f(24, "bold"),
                                          fg=FG, bg=BG_CARD)
        self._lbl_month_total.pack(anchor="w", pady=(4, 0))

        row = tk.Frame(f, bg=BG)
        row.pack(fill=tk.X, pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ul_card = _Card(row, padx=16, pady=14)
        ul_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tk.Label(ul_card, text="↑  UPLOAD", font=_f(8), fg=ACCENT_UP,
                 bg=BG_CARD).pack(anchor="w")
        self._lbl_month_up = tk.Label(ul_card, text="—", font=_f(14, "bold"),
                                       fg=FG, bg=BG_CARD)
        self._lbl_month_up.pack(anchor="w", pady=(6, 0))

        dn_card = _Card(row, padx=16, pady=14)
        dn_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tk.Label(dn_card, text="↓  DOWNLOAD", font=_f(8), fg=ACCENT_DN,
                 bg=BG_CARD).pack(anchor="w")
        self._lbl_month_dn = tk.Label(dn_card, text="—", font=_f(14, "bold"),
                                       fg=FG, bg=BG_CARD)
        self._lbl_month_dn.pack(anchor="w", pady=(6, 0))

        peak_card = _Card(f, padx=16, pady=14)
        peak_card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(peak_card, text="PEAK SPEEDS", font=_f(8),
                 fg=FG_DIM, bg=BG_CARD).pack(anchor="w", pady=(0, 10))
        prows = tk.Frame(peak_card, bg=BG_CARD)
        prows.pack(fill=tk.X)
        prows.columnconfigure(1, weight=1)
        self._lbl_month_peak_up = self._stat_row(prows, "Peak ↑ Upload",  0)
        self._lbl_month_peak_dn = self._stat_row(prows, "Peak ↓ Download",1)

        days_card = _Card(f, padx=16, pady=12)
        days_card.pack(fill=tk.X)
        drow = tk.Frame(days_card, bg=BG_CARD)
        drow.pack(fill=tk.X)
        tk.Label(drow, text="Days tracked", font=_f(9), fg=FG_DIM,
                 bg=BG_CARD).pack(side=tk.LEFT)
        self._lbl_month_days = tk.Label(drow, text="—", font=_f(9, "bold"),
                                         fg=FG, bg=BG_CARD)
        self._lbl_month_days.pack(side=tk.RIGHT)

        return f

    def _stat_row(self, parent: tk.Frame, label: str, row: int) -> tk.Label:
        tk.Label(parent, text=label, font=_f(9), fg=FG_DIM,
                 bg=BG_CARD).grid(row=row, column=0, sticky="w", pady=3)
        val = tk.Label(parent, text="—", font=_f(9, "bold"),
                       fg=FG, bg=BG_CARD)
        val.grid(row=row, column=1, sticky="e", pady=3)
        return val

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, key: str) -> None:
        self._tab_var.set(key)
        for k, lbl in self._tabs.items():
            lbl.config(fg=FG if k == key else FG_DIM,
                       font=_f(10, "bold") if k == key else _f(10))
        # Hide all frames, show selected
        self._today_frame.pack_forget()
        self._month_frame.pack_forget()
        frame = self._today_frame if key == "today" else self._month_frame
        frame.pack(fill=tk.BOTH, expand=True)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        today = date.today()

        d = self._repo.get_daily(today)
        if d:
            self._lbl_today_total.config(text=_fmt_bytes(d.total_bytes))
            self._lbl_today_up.config(text=_fmt_bytes(d.bytes_sent))
            self._lbl_today_dn.config(text=_fmt_bytes(d.bytes_recv))
            self._lbl_today_avg.config(text=_fmt_speed(d.avg_total_speed))
            self._lbl_today_max_up.config(text=_fmt_speed(d.max_up_speed))
            self._lbl_today_max_dn.config(text=_fmt_speed(d.max_down_speed))
            h = d.active_seconds // 3600
            m = (d.active_seconds % 3600) // 60
            s = d.active_seconds % 60
            self._lbl_today_time.config(text=f"{h:02d}h {m:02d}m {s:02d}s")
        else:
            for lbl in (self._lbl_today_total, self._lbl_today_up,
                        self._lbl_today_dn, self._lbl_today_avg,
                        self._lbl_today_max_up, self._lbl_today_max_dn,
                        self._lbl_today_time):
                lbl.config(text="—")

        m_ = self._repo.get_monthly(today.year, today.month)
        self._lbl_month_total.config(text=_fmt_bytes(m_.total_bytes))
        self._lbl_month_up.config(text=_fmt_bytes(m_.bytes_sent))
        self._lbl_month_dn.config(text=_fmt_bytes(m_.bytes_recv))
        self._lbl_month_peak_up.config(text=_fmt_speed(m_.max_up_speed))
        self._lbl_month_peak_dn.config(text=_fmt_speed(m_.max_down_speed))
        self._lbl_month_days.config(text=str(m_.days_tracked))


# ── Reusable widgets ──────────────────────────────────────────────────────────

class _Card(tk.Frame):
    """A dark surface card with a subtle border."""

    def __init__(self, parent: tk.Widget, padx: int = 12, pady: int = 12, **kw) -> None:
        super().__init__(parent, bg=BORDER, **kw)
        self._inner = tk.Frame(self, bg=BG_CARD, padx=padx, pady=pady)
        self._inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    def __getattr__(self, name: str):
        # Delegate pack/grid calls to inner frame transparently for child widgets
        return getattr(self._inner, name)


class _Btn(tk.Frame):
    """Flat button with hover effect."""

    def __init__(self, parent: tk.Widget, text: str, command=None,
                 primary: bool = False) -> None:
        bg     = ACCENT_MAIN if primary else "#2e2e2e"
        bg_hov = "#9b8df9"   if primary else "#3a3a3a"
        fg_    = FG
        super().__init__(parent, bg=bg, cursor="hand2")
        self._bg, self._bg_hov = bg, bg_hov
        self._lbl = tk.Label(self, text=text, font=_f(9), fg=fg_,
                             bg=bg, padx=14, pady=5)
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind("<Enter>",    lambda e: self._hover(True))
            w.bind("<Leave>",    lambda e: self._hover(False))
            w.bind("<Button-1>", lambda e: command() if command else None)

    def _hover(self, on: bool) -> None:
        c = self._bg_hov if on else self._bg
        self.config(bg=c)
        self._lbl.config(bg=c)
