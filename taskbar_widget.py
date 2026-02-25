#!/usr/bin/env python3
"""
Internet Speed Monitor - Taskbar Embedded Widget
Implementation based on TrafficMonitor's Win11TaskbarDlg approach:
  - SetParent into Shell_TrayWnd directly
  - Position relative to TrayNotifyWnd (left of notification area)
  - WS_EX_LAYERED + SetLayeredWindowAttributes for transparency
  - Fallback to overlay with absolute positioning if SetParent fails
"""

import ctypes
import ctypes.wintypes as wintypes
import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import psutil
import sys
import atexit
import signal

# ── Win32 constants & API ────────────────────────────────────────────────────

user32 = ctypes.windll.user32

GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CLIPCHILDREN = 0x02000000
WS_CLIPSIBLINGS = 0x04000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
LWA_COLORKEY = 0x00000001
HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

for fn, argt, rest in [
    (user32.FindWindowW, [wintypes.LPCWSTR, wintypes.LPCWSTR], wintypes.HWND),
    (user32.FindWindowExW, [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR], wintypes.HWND),
    (user32.SetParent, [wintypes.HWND, wintypes.HWND], wintypes.HWND),
    (user32.GetWindowLongW, [wintypes.HWND, ctypes.c_int], ctypes.c_long),
    (user32.SetWindowLongW, [wintypes.HWND, ctypes.c_int, ctypes.c_long], ctypes.c_long),
    (user32.MoveWindow, [wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.BOOL], wintypes.BOOL),
    (user32.GetWindowRect, [wintypes.HWND, ctypes.POINTER(wintypes.RECT)], wintypes.BOOL),
    (user32.ShowWindow, [wintypes.HWND, ctypes.c_int], wintypes.BOOL),
    (user32.SetWindowPos, [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT], wintypes.BOOL),
    (user32.SetLayeredWindowAttributes, [wintypes.HWND, wintypes.DWORD, wintypes.BYTE, wintypes.DWORD], wintypes.BOOL),
    (user32.InvalidateRect, [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL], wintypes.BOOL),
    (user32.GetParent, [wintypes.HWND], wintypes.HWND),
    (user32.GetForegroundWindow, [], wintypes.HWND),
]:
    fn.argtypes = argt
    fn.restype = rest


def _get_rect(hwnd):
    """Return (left, top, right, bottom) for a window handle."""
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


# ── Widget ───────────────────────────────────────────────────────────────────

class TaskbarWidget:
    """Speed monitor widget embedded in the Windows taskbar (Win11 style)."""

    WIDGET_WIDTH = 85
    WIDGET_HEIGHT = 40
    # Color key for transparency — almost-black that won't clash with text
    TRANS_COLOR = "#010101"
    TRANS_COLOR_INT = 0x00010101  # COLORREF format for Win32 (0x00BBGGRR)
    TEXT_COLOR = "#ffffff"  # Crisp white
    UL_COLOR = "#f39c12"    # Orange/Amber for UP
    DL_COLOR = "#00e5ff"    # Cyan/Teal for DN

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NetSpeed")
        self.running = True
        self.embedded = False

        # Taskbar handles
        self.h_taskbar = None
        self.h_notify = None
        self.h_start = None

        # Network counters
        net = psutil.net_io_counters()
        self.last_recv = net.bytes_recv
        self.last_sent = net.bytes_sent

        # Build UI before any Win32 manipulation
        self._create_ui()

        # Get native HWND (must happen before overrideredirect)
        self.root.update()
        self.hwnd = self._get_hwnd()
        print(f"[DEBUG] HWND: {self.hwnd}")

        # Remove title bar / borders
        self.root.overrideredirect(True)
        self.root.update()
        self.hwnd = self._get_hwnd()  # re-fetch after overrideredirect
        print(f"[DEBUG] HWND after overrideredirect: {self.hwnd}")

        # Apply WS_EX_TOOLWINDOW (hide from alt-tab)
        ex = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        ex |= WS_EX_TOOLWINDOW
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ctypes.c_long(ex))

        # Find taskbar components
        self._find_taskbar()

        # Attempt embedding
        if self.h_taskbar:
            self.embedded = self._embed()

        if self.embedded:
            self._apply_layered_transparency()
            self._position_on_taskbar()
        else:
            print("[INFO] Fallback to overlay mode.")
            self._setup_overlay()

        user32.ShowWindow(self.hwnd, 5)  # SW_SHOW

        # Cleanup on exit
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, lambda *_: self.exit_app())

        # Start speed monitoring
        threading.Thread(target=self._monitor_loop, daemon=True).start()

        # Periodic position adjustment
        self._adjust_job()

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _get_hwnd(self):
        frame_id = self.root.wm_frame()
        if frame_id and frame_id != "0x0":
            return int(frame_id, 16)
        return self.root.winfo_id()

    def _find_taskbar(self):
        """Locate Shell_TrayWnd, TrayNotifyWnd, and Start button."""
        self.h_taskbar = user32.FindWindowW("Shell_TrayWnd", None)
        if not self.h_taskbar:
            print("[WARN] Shell_TrayWnd not found.")
            return
        self.h_notify = user32.FindWindowExW(self.h_taskbar, None, "TrayNotifyWnd", None)
        self.h_start = user32.FindWindowExW(self.h_taskbar, None, "Start", None)
        print(f"[DEBUG] Taskbar: {self.h_taskbar}, Notify: {self.h_notify}, Start: {self.h_start}")

    def _embed(self):
        """SetParent into Shell_TrayWnd (Win11 approach)."""
        result = user32.SetParent(self.hwnd, self.h_taskbar)
        if not result:
            print("[WARN] SetParent failed.")
            return False

        # Change style to WS_CHILD
        style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)
        style = (style & ~WS_POPUP) | WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS
        user32.SetWindowLongW(self.hwnd, GWL_STYLE, ctypes.c_long(style))

        print("[OK] Embedded in taskbar (Win11 style).")
        return True

    def _position_on_taskbar(self):
        """Position widget left of the notification area (like TrafficMonitor Win11)."""
        if not self.h_taskbar:
            return

        tb_l, tb_t, tb_r, tb_b = _get_rect(self.h_taskbar)
        tb_w = tb_r - tb_l
        tb_h = tb_b - tb_t

        # Calculate X position: left of the notification area
        notify_x = 0
        if self.h_notify:
            nl, nt, nr, nb = _get_rect(self.h_notify)
            notify_x = nl  # absolute screen X of notification area
        else:
            # Fallback: assume 88px from right edge for clock area
            notify_x = tb_r - 88

        if self.embedded:
            # When embedded (child of taskbar), coordinates are relative to parent
            widget_x = (notify_x - tb_l) - self.WIDGET_WIDTH - 2
        else:
            # Overlay: use absolute screen coordinates
            widget_x = notify_x - self.WIDGET_WIDTH - 2

        # Calculate Y position: vertically centered in taskbar
        if self.h_start:
            sl, st, sr, sb = _get_rect(self.h_start)
            start_h = sb - st
            start_rel_top = st - tb_t
            widget_y = (start_h - self.WIDGET_HEIGHT) // 2 + (tb_h - start_h)
        else:
            widget_y = (tb_h - self.WIDGET_HEIGHT) // 2

        if self.embedded:
            user32.MoveWindow(self.hwnd, widget_x, widget_y,
                              self.WIDGET_WIDTH, self.WIDGET_HEIGHT, True)
        else:
            abs_x = widget_x if not self.embedded else widget_x + tb_l
            abs_y = tb_t + widget_y
            self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}+{abs_x}+{abs_y}")

    def _apply_layered_transparency(self):
        """WS_EX_LAYERED + LWA_COLORKEY to make TRANS_COLOR pixels invisible."""
        ex = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        ex |= WS_EX_LAYERED
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ctypes.c_long(ex))
        user32.SetLayeredWindowAttributes(self.hwnd, self.TRANS_COLOR_INT, 0, LWA_COLORKEY)

    def _setup_overlay(self):
        """Fallback overlay: position near taskbar, always on top."""
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", self.TRANS_COLOR)
        self._position_on_taskbar()

    def _adjust_job(self):
        """Periodically reposition (handles taskbar resize, notification area changes)."""
        if not self.running:
            return
        try:
            self._position_on_taskbar()
            if self.embedded:
                user32.ShowWindow(self.hwnd, 5)
            elif not self.embedded:
                # Fallback: re-assert topmost if the taskbar has focus
                fg = user32.GetForegroundWindow()
                if fg == self.h_taskbar:
                    user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
        except Exception:
            pass
        self.root.after(2000, self._adjust_job)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _create_ui(self):
        self.root.configure(bg=self.TRANS_COLOR)
        # Tightly constrain width so left and right anchors don't space out
        self.root.geometry(f"85x{self.WIDGET_HEIGHT}")

        container = tk.Frame(self.root, bg=self.TRANS_COLOR)
        # `expand=True` without `fill` perfectly centers the grid inside the 40px height
        container.pack(expand=True)

        # TrafficMonitor exact font matching (Skin 11 standard)
        sys_font = ("Segoe UI Semibold", 10)
        arrow_fnt = ("Segoe UI Semibold", 9) 
        
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=0)

        # Upload row: Notice bd=0, pady=0 to tightly pack the rows
        tk.Label(container, text="↑", font=arrow_fnt, fg=self.UL_COLOR,
                 bg=self.TRANS_COLOR, bd=0, pady=0).grid(row=0, column=0, sticky="e", padx=(2, 2), pady=0)
        self.ul_val = tk.Label(container, text="0 B/s", font=sys_font,
                               fg=self.TEXT_COLOR, bg=self.TRANS_COLOR,
                               anchor="w", bd=0, pady=0)
        self.ul_val.grid(row=0, column=1, sticky="w", padx=(0, 2), pady=0)

        # Download row: Notice bd=0, pady=0
        tk.Label(container, text="↓", font=arrow_fnt, fg=self.DL_COLOR,
                 bg=self.TRANS_COLOR, bd=0, pady=0).grid(row=1, column=0, sticky="e", padx=(2, 2), pady=0)
        self.dl_val = tk.Label(container, text="0 B/s", font=sys_font,
                               fg=self.TEXT_COLOR, bg=self.TRANS_COLOR,
                               anchor="w", bd=0, pady=0)
        self.dl_val.grid(row=1, column=1, sticky="w", padx=(0, 2), pady=0)

        # Right-click context menu
        self.menu = tk.Menu(self.root, tearoff=0, bg="#2b2b2b", fg="#ffffff",
                            activebackground="#4d4d4d", activeforeground="#ffffff",
                            font=("Segoe UI", 9), relief="flat", borderwidth=1)
        self.menu.add_command(label="Exit", command=self.exit_app)

        for w in (container, self.ul_val, self.dl_val):
            w.bind("<Button-3>", self._show_menu)

    def _show_menu(self, e):
        self.menu.post(e.x_root, e.y_root)

    # ── Speed monitoring ──────────────────────────────────────────────────────

    @staticmethod
    def _fmt(bps):
        if bps >= 1024 ** 3:
            return f"{bps / 1024**3:.2f} GB/s"
        if bps >= 1024 ** 2:
            return f"{bps / 1024**2:.2f} MB/s"
        if bps >= 1024:
            return f"{bps / 1024:.2f} KB/s"
        return f"{bps:.0f}  B/s"

    def _monitor_loop(self):
        while self.running:
            try:
                n = psutil.net_io_counters()
                dl = max(0, n.bytes_recv - self.last_recv)
                ul = max(0, n.bytes_sent - self.last_sent)
                self.last_recv = n.bytes_recv
                self.last_sent = n.bytes_sent
                self.root.after(0, self._update_labels, self._fmt(dl), self._fmt(ul))
            except Exception:
                pass
            time.sleep(1)

    def _update_labels(self, dl, ul):
        try:
            self.dl_val.config(text=dl)
            self.ul_val.config(text=ul)
        except tk.TclError:
            pass

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _cleanup(self):
        # No cleanup needed for Win11 approach (no taskbar resize was done)
        pass

    def exit_app(self):
        self.running = False
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("Taskbar Speed Monitor (TrafficMonitor Win11 style)")
    print("==================================================")
    print("Right-click widget → Exit | Close this console to quit")
    print()
    TaskbarWidget().run()
