"""Statistics Window — Presentation layer.

Premium dark-themed window displaying daily, monthly, and custom-range
network usage statistics for SpeedMonitor using CustomTkinter and Matplotlib.
"""

from __future__ import annotations

import csv
import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from application.services.speed_monitor_service import SpeedMonitorService
    from domain.entities.network_usage import SpeedSnapshot
    from domain.interfaces.usage_repository import UsageRepository

# ── Theme Configuration ─────────────────────────────────────────────────

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Custom Colors
BG_SURFACE = "#1a1a1a"
BG_CARD = "#222222"
ACCENT_UP = "#f39c12"   # orange — upload
ACCENT_DN = "#00e5ff"   # cyan   — download
ACCENT_MAIN = "#7c6af7"   # purple — primary accent

# ── Helpers ─────────────────────────────────────────────────────────────


def _fmt_bytes(b: int | float) -> str:
    if b >= 1024 ** 3:
        return f"{b / 1024**3:.2f} GB"
    if b >= 1024 ** 2:
        return f"{b / 1024**2:.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b:.0f} B"


def _fmt_speed(bps: float) -> str:
    if bps >= 1024 ** 3:
        return f"{bps / 1024**3:.2f} GB/s"
    if bps >= 1024 ** 2:
        return f"{bps / 1024**2:.2f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.2f} KB/s"
    return f"{bps:.0f} B/s"


# ── Main Window ─────────────────────────────────────────────────────────

class StatisticsWindow:
    """Premium statistics popup window using CustomTkinter."""

    WIDTH = 540
    HEIGHT = 700

    def __init__(
            self,
            parent: tk.Tk | ctk.CTk,
            service: "SpeedMonitorService",
            repo: "UsageRepository") -> None:
        self._service = service
        self._repo = repo
        self._win = ctk.CTkToplevel(parent)
        self._win.withdraw()  # Withdraw immediately to prevent flickering
        self._win.title("SpeedMonitor — Statistics")
        self._win.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)
        self._win.attributes("-alpha", 0.0)  # Make fully transparent initially
        self._win.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._build()
        self._refresh()

        self._service.subscribe(self._on_live_speed)

        # Center on screen and reveal
        self._win.update_idletasks()
        sw = self._win.winfo_screenwidth()
        sh = self._win.winfo_screenheight()
        x = (sw - self.WIDTH) // 2
        y = (sh - self.HEIGHT) // 2
        self._win.geometry(f"+{x}+{y}")

        self._win.deiconify()
        self._fade_in()

    def _fade_in(self) -> None:
        alpha = self._win.attributes("-alpha")
        if alpha < 1.0:
            alpha += 0.08
            self._win.attributes("-alpha", min(1.0, alpha))
            self._win.after(16, self._fade_in)
        else:
            self._win.lift()
            self._win.focus_force()

    def _on_closing(self) -> None:
        self._service.unsubscribe(self._on_live_speed)
        self._fade_out()

    def _fade_out(self) -> None:
        try:
            alpha = self._win.attributes("-alpha")
            if alpha > 0.0:
                alpha -= 0.15
                self._win.attributes("-alpha", max(0.0, alpha))
                self._win.after(16, self._fade_out)
            else:
                self._win.destroy()
        except tk.TclError:
            pass

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Header bar ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(
            self._win,
            height=70,
            corner_radius=0,
            fg_color=BG_SURFACE)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Title
        title_lbl = ctk.CTkLabel(header, text="SpeedMonitor Statistics",
                                 font=ctk.CTkFont(size=18, weight="bold"))
        title_lbl.pack(side=tk.LEFT, padx=(20, 10), pady=20)

        # Date
        date_lbl = ctk.CTkLabel(header, text=date.today().strftime(
            "%B %d, %Y"), font=ctk.CTkFont(size=12), text_color="gray")
        date_lbl.pack(side=tk.LEFT, padx=0)

        # Live Speed
        live_frame = ctk.CTkFrame(header, fg_color="transparent")
        live_frame.pack(side=tk.RIGHT, padx=20)
        self._lbl_live_up = ctk.CTkLabel(
            live_frame,
            text="↑ 0 B/s",
            font=ctk.CTkFont(
                size=13,
                weight="bold"),
            text_color=ACCENT_UP)
        self._lbl_live_up.pack(side=tk.LEFT, padx=5)
        self._lbl_live_dn = ctk.CTkLabel(
            live_frame,
            text="↓ 0 B/s",
            font=ctk.CTkFont(
                size=13,
                weight="bold"),
            text_color=ACCENT_DN)
        self._lbl_live_dn.pack(side=tk.LEFT, padx=5)

        # ── Tabview ─────────────────────────────────────────────────────────
        self._tabview = ctk.CTkTabview(self._win, corner_radius=10)
        self._tabview.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 5))

        self._tab_today = self._tabview.add("Today")
        self._tab_month = self._tabview.add("This Month")
        self._tab_trends = self._tabview.add("Trends (30 Days)")

        self._build_today_tab()
        self._build_month_tab()
        self._build_trends_tab()

        # ── Footer ──────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(
            self._win,
            height=60,
            corner_radius=0,
            fg_color="transparent")
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))
        footer.pack_propagate(False)

        btn_export = ctk.CTkButton(footer, text="Export CSV", width=100,
                                   fg_color="#2e2e2e", hover_color="#3a3a3a",
                                   command=self._export_csv)
        btn_export.pack(side=tk.LEFT, padx=20)

        btn_refresh = ctk.CTkButton(footer, text="Refresh", width=100,
                                    fg_color="#2e2e2e", hover_color="#3a3a3a",
                                    command=self._refresh)
        btn_refresh.pack(side=tk.RIGHT, padx=5)

        btn_close = ctk.CTkButton(footer, text="Close", width=100,
                                  fg_color=ACCENT_MAIN, hover_color="#9b8df9",
                                  command=self._on_closing)
        btn_close.pack(side=tk.RIGHT, padx=20)

    def _build_today_tab(self) -> None:
        f = self._tab_today

        # Hero Total
        hero = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        hero.pack(fill=tk.X, pady=(10, 10), padx=10)
        ctk.CTkLabel(
            hero,
            text="Total Usage Today",
            text_color="gray",
            font=ctk.CTkFont(
                size=12)).pack(
            anchor="w",
            padx=20,
            pady=(
                15,
                0))
        self._lbl_today_total = ctk.CTkLabel(
            hero, text="—", font=ctk.CTkFont(
                size=32, weight="bold"))
        self._lbl_today_total.pack(anchor="w", padx=20, pady=(0, 15))

        # Up/Down Row
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill=tk.X, pady=(0, 10), padx=10)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ul_card = ctk.CTkFrame(
            row,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        ul_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(
            ul_card,
            text="↑ UPLOAD",
            text_color=ACCENT_UP,
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                15,
                0))
        self._lbl_today_up = ctk.CTkLabel(
            ul_card, text="—", font=ctk.CTkFont(
                size=20, weight="bold"))
        self._lbl_today_up.pack(anchor="w", padx=15, pady=(0, 15))

        dn_card = ctk.CTkFrame(
            row,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        dn_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(
            dn_card,
            text="↓ DOWNLOAD",
            text_color=ACCENT_DN,
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                15,
                0))
        self._lbl_today_dn = ctk.CTkLabel(
            dn_card, text="—", font=ctk.CTkFont(
                size=20, weight="bold"))
        self._lbl_today_dn.pack(anchor="w", padx=15, pady=(0, 15))

        # Speed stats grid
        speed_card = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        speed_card.pack(fill=tk.X, pady=(0, 10), padx=10)
        ctk.CTkLabel(
            speed_card,
            text="SPEED METRICS",
            text_color="gray",
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                10,
                5))

        self._lbl_today_avg = self._stat_row(speed_card, "Avg Speed", 0)
        self._lbl_today_max_up = self._stat_row(speed_card, "Peak ↑ Upload", 1)
        self._lbl_today_max_dn = self._stat_row(
            speed_card, "Peak ↓ Download", 2)

        # Active time
        time_card = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        time_card.pack(fill=tk.X, pady=(0, 10), padx=10)
        ctk.CTkLabel(
            time_card,
            text="MONITORING TIME",
            text_color="gray",
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                10,
                0))
        self._lbl_today_time = ctk.CTkLabel(
            time_card, text="—", font=ctk.CTkFont(size=14))
        self._lbl_today_time.pack(anchor="w", padx=15, pady=(0, 10))

    def _build_month_tab(self) -> None:
        f = self._tab_month

        hero = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        hero.pack(fill=tk.X, pady=(10, 10), padx=10)
        ctk.CTkLabel(
            hero,
            text=f"Total — {date.today().strftime('%B %Y')}",
            text_color="gray",
            font=ctk.CTkFont(
                size=12)).pack(
            anchor="w",
            padx=20,
            pady=(
                15,
                0))
        self._lbl_month_total = ctk.CTkLabel(
            hero, text="—", font=ctk.CTkFont(
                size=32, weight="bold"))
        self._lbl_month_total.pack(anchor="w", padx=20, pady=(0, 15))

        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill=tk.X, pady=(0, 10), padx=10)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        ul_card = ctk.CTkFrame(
            row,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        ul_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(
            ul_card,
            text="↑ UPLOAD",
            text_color=ACCENT_UP,
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                15,
                0))
        self._lbl_month_up = ctk.CTkLabel(
            ul_card, text="—", font=ctk.CTkFont(
                size=20, weight="bold"))
        self._lbl_month_up.pack(anchor="w", padx=15, pady=(0, 15))

        dn_card = ctk.CTkFrame(
            row,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        dn_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(
            dn_card,
            text="↓ DOWNLOAD",
            text_color=ACCENT_DN,
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                15,
                0))
        self._lbl_month_dn = ctk.CTkLabel(
            dn_card, text="—", font=ctk.CTkFont(
                size=20, weight="bold"))
        self._lbl_month_dn.pack(anchor="w", padx=15, pady=(0, 15))

        peak_card = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        peak_card.pack(fill=tk.X, pady=(0, 10), padx=10)
        ctk.CTkLabel(
            peak_card,
            text="PEAK SPEEDS",
            text_color="gray",
            font=ctk.CTkFont(
                size=11,
                weight="bold")).pack(
            anchor="w",
            padx=15,
            pady=(
                10,
                5))
        self._lbl_month_peak_up = self._stat_row(peak_card, "Peak ↑ Upload", 0)
        self._lbl_month_peak_dn = self._stat_row(
            peak_card, "Peak ↓ Download", 1)

        days_card = ctk.CTkFrame(
            f,
            corner_radius=8,
            fg_color=BG_CARD,
            border_width=1,
            border_color="#333333")
        days_card.pack(fill=tk.X, pady=(0, 10), padx=10)
        self._lbl_month_days = self._stat_row(days_card, "Days tracked", 0)

    def _build_trends_tab(self) -> None:
        self._chart_frame = ctk.CTkFrame(
            self._tab_trends, fg_color="transparent")
        self._chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Plot will be rendered in _refresh_charts()

    def _stat_row(
            self,
            parent: ctk.CTkFrame,
            label: str,
            row: int) -> ctk.CTkLabel:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.X, padx=15, pady=(0, 5))

        ctk.CTkLabel(
            container,
            text=label,
            text_color="gray",
            font=ctk.CTkFont(
                size=13)).pack(
            side=tk.LEFT)
        val = ctk.CTkLabel(
            container, text="—", font=ctk.CTkFont(
                size=13, weight="bold"))
        val.pack(side=tk.RIGHT)

        return val

    # ── Live Speed ──────────────────────────────────────────────────────────

    def _on_live_speed(self, snap: SpeedSnapshot) -> None:
        try:
            self._win.after(0, self._update_live_labels, snap)
        except Exception:
            pass

    def _update_live_labels(self, snap: SpeedSnapshot) -> None:
        try:
            self._lbl_live_up.configure(text=f"↑ {_fmt_speed(snap.up_speed)}")
            self._lbl_live_dn.configure(
                text=f"↓ {_fmt_speed(snap.down_speed)}")
        except Exception:
            pass

    # ── Data & Charts ───────────────────────────────────────────────────────

    def _refresh(self) -> None:
        today = date.today()

        # Update Today
        d = self._repo.get_daily(today)
        if d:
            self._lbl_today_total.configure(text=_fmt_bytes(d.total_bytes))
            self._lbl_today_up.configure(text=_fmt_bytes(d.bytes_sent))
            self._lbl_today_dn.configure(text=_fmt_bytes(d.bytes_recv))
            self._lbl_today_avg.configure(text=_fmt_speed(d.avg_total_speed))
            self._lbl_today_max_up.configure(text=_fmt_speed(d.max_up_speed))
            self._lbl_today_max_dn.configure(text=_fmt_speed(d.max_down_speed))
            h = d.active_seconds // 3600
            m = (d.active_seconds % 3600) // 60
            s = d.active_seconds % 60
            self._lbl_today_time.configure(text=f"{h:02d}h {m:02d}m {s:02d}s")
        else:
            for lbl in (self._lbl_today_total, self._lbl_today_up,
                        self._lbl_today_dn, self._lbl_today_avg,
                        self._lbl_today_max_up, self._lbl_today_max_dn,
                        self._lbl_today_time):
                lbl.configure(text="—")

        # Update Month
        m_ = self._repo.get_monthly(today.year, today.month)
        self._lbl_month_total.configure(text=_fmt_bytes(m_.total_bytes))
        self._lbl_month_up.configure(text=_fmt_bytes(m_.bytes_sent))
        self._lbl_month_dn.configure(text=_fmt_bytes(m_.bytes_recv))
        self._lbl_month_peak_up.configure(text=_fmt_speed(m_.max_up_speed))
        self._lbl_month_peak_dn.configure(text=_fmt_speed(m_.max_down_speed))
        self._lbl_month_days.configure(text=str(m_.days_tracked))

        # Update Charts
        self._refresh_charts(today)

    def _refresh_charts(self, today: date) -> None:
        # Clear existing charts
        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        start_date = today - timedelta(days=29)
        history = self._repo.get_range(start_date, today)

        # Matplotlib Figure
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=BG_CARD)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_CARD)

        # Style tweaks
        ax.spines['bottom'].set_color('gray')
        ax.spines['top'].set_color(BG_CARD)
        ax.spines['right'].set_color(BG_CARD)
        ax.spines['left'].set_color('gray')
        ax.tick_params(axis='x', colors='gray')
        ax.tick_params(axis='y', colors='gray')

        days = []
        down_data = []
        up_data = []

        # Fill missing days with 0
        history_dict = {d.day: d for d in history}

        for i in range(30):
            d = start_date + timedelta(days=i)
            days.append(d.strftime("%d"))
            if d in history_dict:
                # Convert to MB for display
                down_data.append(history_dict[d].bytes_recv / (1024 * 1024))
                up_data.append(history_dict[d].bytes_sent / (1024 * 1024))
            else:
                down_data.append(0)
                up_data.append(0)

        # Plot stacked bar chart
        ax.bar(
            days,
            down_data,
            label='Download (MB)',
            color=ACCENT_DN,
            alpha=0.8)
        ax.bar(
            days,
            up_data,
            bottom=down_data,
            label='Upload (MB)',
            color=ACCENT_UP,
            alpha=0.8)

        # Only show a few x-axis labels to avoid crowding
        x_ticks = [i for i in range(0, 30, 5)]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([days[i] for i in x_ticks])
        ax.set_ylabel('Data (MB)', color='gray')

        fig.legend(
            loc="upper right",
            facecolor=BG_CARD,
            edgecolor='none',
            labelcolor='white')
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ── Export CSV ───────────────────────────────────────────────────────────

    def _export_csv(self) -> None:
        file_path = filedialog.asksaveasfilename(
            parent=self._win,
            title="Export Usage Statistics",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"speedmonitor_usage_{date.today().strftime('%Y%m%d')}.csv"
        )

        if not file_path:
            return

        try:
            # Export all available data (e.g., last 365 days)
            start_date = date.today() - timedelta(days=365)
            data = self._repo.get_range(start_date, date.today())

            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date",
                                 "Upload Bytes",
                                 "Download Bytes",
                                 "Max Upload Speed (B/s)",
                                 "Max Download Speed (B/s)",
                                 "Active Seconds"])
                for d in data:
                    writer.writerow([d.day.isoformat(),
                                     d.bytes_sent,
                                     d.bytes_recv,
                                     d.max_up_speed,
                                     d.max_down_speed,
                                     d.active_seconds])

            messagebox.showinfo(
                "Export Successful",
                f"Data exported to:\n{file_path}",
                parent=self._win)
        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export data:\n{e}",
                parent=self._win)
