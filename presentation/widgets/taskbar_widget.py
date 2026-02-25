"""SpeedMonitor — Taskbar Widget (Presentation layer).

This module contains ONLY UI logic. All business logic is delegated to
the Application layer (SpeedMonitorService).
"""

from __future__ import annotations

import atexit
import signal
import sys
import threading
import tkinter as tk
from typing import TYPE_CHECKING

import pystray
from PIL import Image, ImageDraw

from domain.entities.network_usage import SpeedSnapshot
from infrastructure.system.windows_taskbar import TaskbarHelper

if TYPE_CHECKING:
    from application.services.speed_monitor_service import SpeedMonitorService
    from domain.interfaces.usage_repository import UsageRepository


class TaskbarWidget:
    """Speed monitor widget embedded in the Windows taskbar (Win11 style)."""

    WIDGET_WIDTH = 85
    WIDGET_HEIGHT = 40
    TRANS_COLOR = "#010101"
    TRANS_COLOR_INT = 0x00010101
    TEXT_COLOR = "#ffffff"
    UL_COLOR = "#f39c12"
    DL_COLOR = "#00e5ff"

    def __init__(
        self,
        service: "SpeedMonitorService",
        repo: "UsageRepository",
    ) -> None:
        self._service = service
        self._repo = repo

        self.root = tk.Tk()
        self.root.title("SpeedMonitor")
        self.running = True
        self.embedded = False
        self._hidden = False  # fullscreen-aware visibility state
        self._tray_icon: pystray.Icon | None = None

        self._tb = TaskbarHelper()
        self._create_ui()

        # Get native HWND
        self.root.update()
        self.hwnd = self._get_hwnd()

        # Remove title bar / borders
        self.root.overrideredirect(True)
        self.root.update()
        self.hwnd = self._get_hwnd()

        # Hide from alt-tab
        self._tb.apply_tool_window(self.hwnd)

        # Attempt embedding
        if self._tb.found:
            self.embedded = self._tb.embed(self.hwnd)

        if self.embedded:
            self._tb.apply_transparency(self.hwnd, self.TRANS_COLOR_INT)
            self._position()
        else:
            self._setup_overlay()

        self._tb.show(self.hwnd)

        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, lambda *_: self.exit_app())

        # Wire the service callback
        self._service.subscribe(self._on_speed)
        self._service.start()

        # System tray icon
        self._setup_tray()

        self._adjust_job()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    # ── HWND helper ──────────────────────────────────────────────────────────

    def _get_hwnd(self) -> int:
        frame_id = self.root.wm_frame()
        if frame_id and frame_id != "0x0":
            return int(frame_id, 16)
        return self.root.winfo_id()

    # ── Positioning ──────────────────────────────────────────────────────────

    def _position(self) -> None:
        if not self._tb.found:
            return
        x, y = self._tb.calc_position(
            self.WIDGET_WIDTH, self.WIDGET_HEIGHT, self.embedded)
        if self.embedded:
            self._tb.move(
                self.hwnd,
                x,
                y,
                self.WIDGET_WIDTH,
                self.WIDGET_HEIGHT)
        else:
            from infrastructure.system.windows_taskbar import get_rect
            tb_l, tb_t, *_ = get_rect(self._tb.h_taskbar)
            self.root.geometry(
                f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}+{x}+{tb_t + y}")

    def _setup_overlay(self) -> None:
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", self.TRANS_COLOR)
        self._position()

    def _adjust_job(self) -> None:
        if not self.running:
            return
        try:
            # Fullscreen detection — hide when taskbar is hidden
            if self._tb.is_fullscreen_active():
                if not self._hidden:
                    self._tb.hide(self.hwnd)
                    self._hidden = True
            else:
                if self._hidden:
                    self._tb.show(self.hwnd)
                    self._hidden = False
                self._position()
                if self.embedded:
                    self._tb.show(self.hwnd)
                else:
                    self._tb.ensure_topmost(self.hwnd)
        except Exception:
            pass
        self.root.after(1000, self._adjust_job)

    # ── UI ──────────────────────────────────────────────────────────────────

    def _create_ui(self) -> None:
        self.root.configure(bg=self.TRANS_COLOR)
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}")

        container = tk.Frame(self.root, bg=self.TRANS_COLOR)
        container.pack(expand=True)

        sys_font = ("Segoe UI Semibold", 10)
        arrow_fnt = ("Segoe UI Semibold", 9)

        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=0)

        # Upload row
        tk.Label(container, text="↑", font=arrow_fnt, fg=self.UL_COLOR,
                 bg=self.TRANS_COLOR, bd=0, pady=0).grid(
            row=0, column=0, sticky="e", padx=(2, 2), pady=0)
        self.ul_val = tk.Label(container, text="0 B/s", font=sys_font,
                               fg=self.TEXT_COLOR, bg=self.TRANS_COLOR,
                               anchor="w", bd=0, pady=0)
        self.ul_val.grid(row=0, column=1, sticky="w", padx=(0, 2), pady=0)

        # Download row
        tk.Label(container, text="↓", font=arrow_fnt, fg=self.DL_COLOR,
                 bg=self.TRANS_COLOR, bd=0, pady=0).grid(
            row=1, column=0, sticky="e", padx=(2, 2), pady=0)
        self.dl_val = tk.Label(container, text="0 B/s", font=sys_font,
                               fg=self.TEXT_COLOR, bg=self.TRANS_COLOR,
                               anchor="w", bd=0, pady=0)
        self.dl_val.grid(row=1, column=1, sticky="w", padx=(0, 2), pady=0)

        # Context menu
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#2b2b2b",
            fg="#ffffff",
            activebackground="#4d4d4d",
            activeforeground="#ffffff",
            font=(
                "Segoe UI",
                9),
            relief="flat",
            borderwidth=1)
        self.menu.add_command(
            label="Usage Statistics",
            command=self._show_stats)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)

        for w in (container, self.ul_val, self.dl_val):
            w.bind("<Button-3>", self._show_menu)

    def _show_menu(self, e: tk.Event) -> None:
        self.menu.post(e.x_root, e.y_root)

    def _show_stats(self) -> None:
        from presentation.windows.statistics_window import StatisticsWindow
        StatisticsWindow(self.root, self._service, self._repo)

    # ── Speed callback ───────────────────────────────────────────────────────

    @staticmethod
    def _fmt(bps: int) -> str:
        if bps >= 1024 ** 3:
            return f"{bps / 1024**3:.2f} GB/s"
        if bps >= 1024 ** 2:
            return f"{bps / 1024**2:.2f} MB/s"
        if bps >= 1024:
            return f"{bps / 1024:.2f} KB/s"
        return f"{bps:.0f}  B/s"

    def _on_speed(self, snap: SpeedSnapshot) -> None:
        try:
            self.root.after(0, self._update_labels, snap)
        except Exception:
            pass

    def _update_labels(self, snap: SpeedSnapshot) -> None:
        try:
            self.ul_val.config(text=self._fmt(snap.up_speed))
            self.dl_val.config(text=self._fmt(snap.down_speed))
        except tk.TclError:
            pass

    # ── System tray ─────────────────────────────────────────────────────────

    def _setup_tray(self) -> None:
        """Create a system tray icon with menu options."""
        icon_img = self._create_tray_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Usage Statistics", self._tray_show_stats),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._tray_exit),
        )
        self._tray_icon = pystray.Icon(
            "SpeedMonitor", icon_img, "SpeedMonitor", menu)
        threading.Thread(target=self._tray_icon.run, daemon=True).start()

    @staticmethod
    def _create_tray_icon() -> Image.Image:
        """Generate a polished 64x64 tray icon."""
        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded dark background
        r = 12
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r,
                               fill="#1e1e1e")

        # Thin separator line
        draw.line([(10, 31), (54, 31)], fill="#333333", width=1)

        # Up arrow (orange) — top half
        draw.polygon([(32, 6), (18, 26), (27, 26), (27, 29),
                      (37, 29), (37, 26), (46, 26)], fill="#f39c12")

        # Down arrow (cyan) — bottom half
        draw.polygon([(32, 58), (18, 38), (27, 38), (27, 35),
                      (37, 35), (37, 38), (46, 38)], fill="#00e5ff")

        return img

    def _tray_show_stats(self, icon=None, item=None) -> None:
        self.root.after(0, self._show_stats)

    def _tray_exit(self, icon=None, item=None) -> None:
        self.root.after(0, self.exit_app)

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def _cleanup(self) -> None:
        self._service.stop()
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass

    def exit_app(self) -> None:
        self.running = False
        self._service.stop()
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self) -> None:
        self.root.mainloop()
