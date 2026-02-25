"""Isolates all Win32 / ctypes logic for taskbar embedding — Infrastructure layer."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes

user32 = ctypes.windll.user32

# ── Win32 constants ──────────────────────────────────────────────────────────

GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CLIPSIBLINGS = 0x04000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
LWA_COLORKEY = 0x00000001
HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

# ── Type annotations for Win32 functions ─────────────────────────────────────

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
    (user32.GetParent, [wintypes.HWND], wintypes.HWND),
    (user32.GetForegroundWindow, [], wintypes.HWND),
]:
    fn.argtypes = argt
    fn.restype = rest


def get_rect(hwnd: int) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) for a window handle."""
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


class TaskbarHelper:
    """Finds and interacts with the Windows 11 taskbar."""

    def __init__(self) -> None:
        self.h_taskbar: int = 0
        self.h_notify: int = 0
        self.h_start: int = 0
        self._find()

    def _find(self) -> None:
        self.h_taskbar = user32.FindWindowW("Shell_TrayWnd", None) or 0
        if not self.h_taskbar:
            return
        self.h_notify = user32.FindWindowExW(self.h_taskbar, None, "TrayNotifyWnd", None) or 0
        self.h_start = user32.FindWindowExW(self.h_taskbar, None, "Start", None) or 0

    @property
    def found(self) -> bool:
        return bool(self.h_taskbar)

    def embed(self, hwnd: int) -> bool:
        """SetParent into Shell_TrayWnd."""
        if not self.h_taskbar:
            return False
        result = user32.SetParent(hwnd, self.h_taskbar)
        if not result:
            return False
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style = (style & ~WS_POPUP) | WS_CHILD | WS_VISIBLE | WS_CLIPSIBLINGS
        user32.SetWindowLongW(hwnd, GWL_STYLE, ctypes.c_long(style))
        return True

    def apply_tool_window(self, hwnd: int) -> None:
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex |= WS_EX_TOOLWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ctypes.c_long(ex))

    def apply_transparency(self, hwnd: int, color_ref: int) -> None:
        ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex |= WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ctypes.c_long(ex))
        user32.SetLayeredWindowAttributes(hwnd, color_ref, 0, LWA_COLORKEY)

    def calc_position(self, w: int, h: int, embedded: bool) -> tuple[int, int]:
        """Return (x, y) for the widget, to sit left of the notification area."""
        tb_l, tb_t, tb_r, tb_b = get_rect(self.h_taskbar)
        tb_h = tb_b - tb_t

        if self.h_notify:
            nl, *_ = get_rect(self.h_notify)
            notify_x = nl
        else:
            notify_x = tb_r - 88

        if embedded:
            x = (notify_x - tb_l) - w - 2
        else:
            x = notify_x - w - 2

        if self.h_start:
            sl, st, sr, sb = get_rect(self.h_start)
            start_h = sb - st
            y = (start_h - h) // 2 + (tb_h - start_h)
        else:
            y = (tb_h - h) // 2

        return x, y

    def move(self, hwnd: int, x: int, y: int, w: int, h: int) -> None:
        user32.MoveWindow(hwnd, x, y, w, h, True)

    def show(self, hwnd: int) -> None:
        user32.ShowWindow(hwnd, 5)

    def ensure_topmost(self, hwnd: int) -> None:
        fg = user32.GetForegroundWindow()
        if fg == self.h_taskbar:
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

    def hide(self, hwnd: int) -> None:
        user32.ShowWindow(hwnd, 0)  # SW_HIDE

    def is_fullscreen_active(self) -> bool:
        """Check if the foreground window is fullscreen (taskbar hidden)."""
        fg = user32.GetForegroundWindow()
        if not fg or fg == self.h_taskbar:
            return False
        try:
            fl, ft, fr, fb = get_rect(fg)
            # Get primary monitor dimensions
            screen_w = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            screen_h = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            # Fullscreen = covers the entire screen
            return fl <= 0 and ft <= 0 and fr >= screen_w and fb >= screen_h
        except Exception:
            return False
