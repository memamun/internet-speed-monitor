#!/usr/bin/env python3
"""
Internet Speed Monitor - Taskbar Widget Version
Shows upload/download speeds in a floating widget that can be positioned on the taskbar
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import psutil
import sys


class TaskbarSpeedMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Net Speed")

        # Remove window decorations for a clean look
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        # Window size and position
        self.width = 180
        self.height = 40

        # Position at bottom-right of screen (typical taskbar area)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Default position: bottom-right, above taskbar
        # Adjust based on taskbar position
        self.x = screen_width - self.width - 20
        self.y = screen_height - self.height - 80

        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

        # Make window background transparent
        self.root.attributes('-transparentcolor', '#000001')
        self.root.configure(bg='#000001')

        # Create main frame
        self.frame = tk.Frame(self.root, bg='#1a1a1a', highlightbackground='#444444',
                              highlightthickness=1)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Load custom font or use system font
        try:
            self.speed_font = tkfont.Font(family="Segoe UI", size=10, weight="bold")
            self.arrow_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        except:
            self.speed_font = tkfont.Font(family="Arial", size=10, weight="bold")
            self.arrow_font = tkfont.Font(family="Arial", size=12, weight="bold")

        # Download section
        self.dl_frame = tk.Frame(self.frame, bg='#1a1a1a')
        self.dl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.dl_arrow = tk.Label(self.dl_frame, text="▼", font=self.arrow_font,
                                  fg="#00ff00", bg='#1a1a1a')
        self.dl_arrow.pack(side=tk.LEFT, padx=2)

        self.dl_label = tk.Label(self.dl_frame, text="0 KB/s", font=self.speed_font,
                                  fg="#ffffff", bg='#1a1a1a')
        self.dl_label.pack(side=tk.LEFT, padx=2)

        # Separator
        self.sep = tk.Frame(self.frame, width=1, bg='#444444')
        self.sep.pack(side=tk.LEFT, fill=tk.Y, pady=5)

        # Upload section
        self.ul_frame = tk.Frame(self.frame, bg='#1a1a1a')
        self.ul_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

        self.ul_arrow = tk.Label(self.ul_frame, text="▲", font=self.arrow_font,
                                  fg="#00aaff", bg='#1a1a1a')
        self.ul_arrow.pack(side=tk.LEFT, padx=2)

        self.ul_label = tk.Label(self.ul_frame, text="0 KB/s", font=self.speed_font,
                                  fg="#ffffff", bg='#1a1a1a')
        self.ul_label.pack(side=tk.LEFT, padx=2)

        # Make draggable
        self.frame.bind('<Button-1>', self.start_drag)
        self.frame.bind('<B1-Motion>', self.on_drag)
        self.dl_frame.bind('<Button-1>', self.start_drag)
        self.dl_frame.bind('<B1-Motion>', self.on_drag)
        self.ul_frame.bind('<Button-1>', self.start_drag)
        self.ul_frame.bind('<B1-Motion>', self.on_drag)
        self.dl_label.bind('<Button-1>', self.start_drag)
        self.dl_label.bind('<B1-Motion>', self.on_drag)
        self.ul_label.bind('<Button-1>', self.start_drag)
        self.ul_label.bind('<B1-Motion>', self.on_drag)

        # Right-click menu
        self.menu = tk.Menu(self.root, tearoff=0, bg='#2a2a2a', fg='#ffffff',
                           activebackground='#444444', activeforeground='#ffffff')
        self.menu.add_command(label="Dock to Taskbar (Bottom)", command=self.dock_bottom)
        self.menu.add_command(label="Dock to Taskbar (Top)", command=self.dock_top)
        self.menu.add_command(label="Dock to Taskbar (Right)", command=self.dock_right)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)

        self.frame.bind('<Button-3>', self.show_menu)
        self.dl_label.bind('<Button-3>', self.show_menu)
        self.ul_label.bind('<Button-3>', self.show_menu)

        # Drag state
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Network monitoring
        self.last_bytes_sent = 0
        self.last_bytes_recv = 0
        self.running = True

        net_io = psutil.net_io_counters()
        self.last_bytes_sent = net_io.bytes_sent
        self.last_bytes_recv = net_io.bytes_recv

        # Start monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        # Update display
        self.update_display()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def start_drag(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.start_x = self.x
        self.start_y = self.y

    def on_drag(self, event):
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        self.x = self.start_x + dx
        self.y = self.start_y + dy
        self.root.geometry(f"+{self.x}+{self.y}")

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def dock_bottom(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.x = screen_width - self.width - 100
        self.y = screen_height - self.height - 50
        self.root.geometry(f"+{self.x}+{self.y}")

    def dock_top(self):
        screen_width = self.root.winfo_screenwidth()
        self.x = screen_width - self.width - 100
        self.y = 5
        self.root.geometry(f"+{self.x}+{self.y}")

    def dock_right(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.x = screen_width - self.width - 5
        self.y = screen_height // 2
        self.root.geometry(f"+{self.x}+{self.y}")

    def format_speed(self, speed_bytes):
        if speed_bytes >= 1024 * 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024 * 1024):.1f} GB"
        elif speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.1f} MB"
        elif speed_bytes >= 1024:
            return f"{speed_bytes / 1024:.0f} KB"
        else:
            return f"{speed_bytes:.0f} B"

    def format_speed_with_unit(self, speed_bytes):
        """Format with /s unit"""
        if speed_bytes >= 1024 * 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024 * 1024):.1f} GB/s"
        elif speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.1f} MB/s"
        elif speed_bytes >= 1024:
            return f"{speed_bytes / 1024:.0f} KB/s"
        else:
            return f"{speed_bytes:.0f} B/s"

    def monitor_loop(self):
        while self.running:
            net_io = psutil.net_io_counters()

            dl_speed = max(0, net_io.bytes_recv - self.last_bytes_recv)
            ul_speed = max(0, net_io.bytes_sent - self.last_bytes_sent)

            self.last_bytes_recv = net_io.bytes_recv
            self.last_bytes_sent = net_io.bytes_sent

            # Update labels in main thread
            self.root.after(0, lambda d=dl_speed, u=ul_speed: self.update_labels(d, u))

            time.sleep(1)

    def update_labels(self, dl_speed, ul_speed):
        self.dl_label.config(text=self.format_speed(dl_speed))
        self.ul_label.config(text=self.format_speed(ul_speed))

        # Change color based on speed intensity
        if dl_speed >= 1024 * 1024 * 10:  # > 10 MB/s
            self.dl_arrow.config(fg="#ff6600")  # Orange for high speed
        elif dl_speed >= 1024 * 1024:
            self.dl_arrow.config(fg="#00ff00")  # Green
        else:
            self.dl_arrow.config(fg="#88ff88")  # Light green for low

        if ul_speed >= 1024 * 1024 * 10:
            self.ul_arrow.config(fg="#ff6600")
        elif ul_speed >= 1024 * 1024:
            self.ul_arrow.config(fg="#00aaff")
        else:
            self.ul_arrow.config(fg="#88ccff")

    def update_display(self):
        # Schedule next update (monitoring happens in thread)
        self.root.after(100, self.update_display)

    def exit_app(self):
        self.running = False
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("Starting Taskbar Speed Monitor...")
    print("Drag to position anywhere on screen")
    print("Right-click for menu options (dock, exit)")
    print("Close this window to exit")

    app = TaskbarSpeedMonitor()
    app.run()
