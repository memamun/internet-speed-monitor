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
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_UP)
        self._lbl_live_up.pack(side=tk.LEFT, padx=5)
        self._lbl_live_dn = ctk.CTkLabel(
            live_frame,
            text="↓ 0 B/s",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=ACCENT_DN)
        self._lbl_live_dn.pack(side=tk.LEFT, padx=5)

        # ── Tabview ─────────────────────────────────────────────────────────
        self._tabview = ctk.CTkTabview(self._win, corner_radius=10)
        self._tabview.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 5))

        self._tab_summary = self._tabview.add("Summary")
        self._tab_daily = self._tabview.add("Day Wise Data")

        self._build_summary_tab()
        self._build_daily_tab()

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

    def _build_summary_tab(self) -> None:
        f = self._tab_summary

        # Top Row Cards
        row = ctk.CTkFrame(f, fg_color="transparent")
        row.pack(fill=tk.X, pady=(10, 10), padx=10)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        # Upload Card
        ul_card = ctk.CTkFrame(
            row, corner_radius=8, fg_color=BG_CARD,
            border_width=1, border_color="#333333"
        )
        ul_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        ctk.CTkLabel(
            ul_card, text="↑ TOTAL UPLOAD (MONTH)", text_color=ACCENT_UP,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))
        self._lbl_sum_up = ctk.CTkLabel(
            ul_card, text="—", font=ctk.CTkFont(size=24, weight="bold")
        )
        self._lbl_sum_up.pack(anchor="w", padx=15, pady=(0, 15))

        # Download Card
        dn_card = ctk.CTkFrame(
            row, corner_radius=8, fg_color=BG_CARD,
            border_width=1, border_color="#333333"
        )
        dn_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        ctk.CTkLabel(
            dn_card, text="↓ TOTAL DOWNLOAD (MONTH)", text_color=ACCENT_DN,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))
        self._lbl_sum_dn = ctk.CTkLabel(
            dn_card, text="—", font=ctk.CTkFont(size=24, weight="bold")
        )
        self._lbl_sum_dn.pack(anchor="w", padx=15, pady=(0, 15))

        # Doughnut Chart Frame
        self._chart_frame = ctk.CTkFrame(f, fg_color="transparent")
        self._chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Detailed Stats Below Chart
        stats_frame = ctk.CTkFrame(
            f, corner_radius=8, fg_color=BG_CARD,
            border_width=1, border_color="#333333"
        )
        stats_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

        self._lbl_sum_total = self._stat_row(
            stats_frame, f"Total Data ({date.today().strftime('%B')})", 0)
        self._lbl_sum_peak_up = self._stat_row(
            stats_frame, "Monthly Peak ↑ Upload", 1)
        self._lbl_sum_peak_dn = self._stat_row(
            stats_frame, "Monthly Peak ↓ Download", 2)
        self._lbl_sum_days = self._stat_row(stats_frame, "Days tracked", 3)

    def _build_daily_tab(self) -> None:
        f = self._tab_daily

        import tkinter.ttk as ttk

        # Style the Treeview to match dark theme
        style = ttk.Style(self._win)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=BG_CARD,
            foreground="white",
            rowheight=25,
            fieldbackground=BG_CARD,
            bordercolor="#333333",
            lightcolor="#333333",
            darkcolor="#333333"
        )
        style.map("Treeview", background=[("selected", ACCENT_MAIN)])
        style.configure(
            "Treeview.Heading",
            background=BG_SURFACE,
            foreground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map("Treeview.Heading", background=[("active", "#333333")])

        # Treeview Scrollbar
        tree_frame = ctk.CTkFrame(f, fg_color="transparent")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
            columns=("Date", "Received", "Sent", "Total"),
            show="headings"
        )
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self._tree.yview)

        # Columns Configuration
        self._tree.heading("Date", text="Date")
        self._tree.column("Date", anchor=tk.W, width=120)

        self._tree.heading("Received", text="Received")
        self._tree.column("Received", anchor=tk.E, width=100)

        self._tree.heading("Sent", text="Sent")
        self._tree.column("Sent", anchor=tk.E, width=100)

        self._tree.heading("Total", text="Total")
        self._tree.column("Total", anchor=tk.E, width=100)

    def _stat_row(self, parent: ctk.CTkFrame, label: str, row: int) -> ctk.CTkLabel:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.X, padx=15, pady=(5, 5))

        ctk.CTkLabel(
            container, text=label, text_color="gray", font=ctk.CTkFont(size=13)
        ).pack(side=tk.LEFT)
        val = ctk.CTkLabel(
            container, text="—", font=ctk.CTkFont(size=13, weight="bold")
        )
        val.pack(side=tk.RIGHT)
        return val

    # ── Live Speed ──────────────────────────────────────────────────────────

    def _on_live_speed(self, snap: "SpeedSnapshot") -> None:
        try:
            self._win.after(0, self._update_live_labels, snap)
        except Exception:
            pass

    def _update_live_labels(self, snap: "SpeedSnapshot") -> None:
        try:
            self._lbl_live_up.configure(text=f"↑ {_fmt_speed(snap.up_speed)}")
            self._lbl_live_dn.configure(
                text=f"↓ {_fmt_speed(snap.down_speed)}")
        except Exception:
            pass

    # ── Data & Charts ───────────────────────────────────────────────────────

    def _refresh(self) -> None:
        today = date.today()

        # Update Month Summary
        m_ = self._repo.get_monthly(today.year, today.month)
        self._lbl_sum_total.configure(text=_fmt_bytes(m_.total_bytes))
        self._lbl_sum_up.configure(text=_fmt_bytes(m_.bytes_sent))
        self._lbl_sum_dn.configure(text=_fmt_bytes(m_.bytes_recv))
        self._lbl_sum_peak_up.configure(text=_fmt_speed(m_.max_up_speed))
        self._lbl_sum_peak_dn.configure(text=_fmt_speed(m_.max_down_speed))
        self._lbl_sum_days.configure(text=str(m_.days_tracked))

        # Update Doughnut Chart
        self._refresh_doughnut(m_.bytes_recv, m_.bytes_sent)

        # Update Daily Table
        self._refresh_daily_table()

    def _refresh_doughnut(self, dn_bytes: int, up_bytes: int) -> None:
        # Clear existing charts
        for widget in self._chart_frame.winfo_children():
            widget.destroy()

        # If completely zero, fake some data to show a grey ring
        if dn_bytes == 0 and up_bytes == 0:
            sizes = [1]
            colors = ["#333333"]
            labels = ["No Data"]
        else:
            sizes = [dn_bytes, up_bytes]
            colors = [ACCENT_DN, ACCENT_UP]
            labels = ["", ""]

        fig = Figure(figsize=(4, 4), dpi=100, facecolor=BG_SURFACE)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_SURFACE)

        # Plot Doughnut Chart
        wedges, texts = ax.pie(
            sizes, labels=labels, colors=colors,
            startangle=90, counterclock=False,
            wedgeprops=dict(width=0.4, edgecolor=BG_SURFACE)
        )

        # Add center text
        ax.text(
            0, 0, "DATA RATIO", ha='center', va='center',
            fontsize=12, color='gray', fontweight='bold'
        )

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _refresh_daily_table(self) -> None:
        # Clear existing items
        for item in self._tree.get_children():
            self._tree.delete(item)

        today = date.today()
        start_date = today - timedelta(days=30)
        history = self._repo.get_range(start_date, today)

        # Sort descending by date (newest top)
        history.sort(key=lambda d: d.day, reverse=True)

        for d in history:
            self._tree.insert(
                "", tk.END,
                values=(
                    d.day.strftime("%Y-%m-%d"),
                    _fmt_bytes(d.bytes_recv),
                    _fmt_bytes(d.bytes_sent),
                    _fmt_bytes(d.total_bytes)
                )
            )

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
