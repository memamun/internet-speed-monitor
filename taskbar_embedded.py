#!/usr/bin/env python3
"""
Internet Speed Monitor - Embedded Taskbar Version
Uses Windows API to create a more integrated taskbar experience
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import psutil
import sys


class EmbeddedTaskbarMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NetSpeed")

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Compact size for taskbar integration
        self.width = 160
        self.height = 30

        # Detect taskbar position and place widget accordingly
        self.taskbar_pos = self.detect_taskbar_position()
        self.x, self.y = self.calculate_position()

        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

        # Window settings for taskbar-like appearance
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', '#000000')
        self.root.configure(bg='#000000')

        # Main container with Windows-style appearance
        self.container = tk.Frame(
            self.root,
            bg='#2b2b2b',
            highlightbackground='#404040',
            highlightthickness=1
        )
        self.container.pack(fill=tk.BOTH, expand=True)

        # Fonts
        self.font_arrows = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.font_speed = tkfont.Font(family="Segoe UI", size=9, weight="normal")

        # Download widget
        self.dl_widget = tk.Frame(self.container, bg='#2b2b2b', padx=6)
        self.dl_widget.pack(side=tk.LEFT, fill=tk.Y)

        self.dl_arrow = tk.Label(
            self.dl_widget,
            text="▼",
            font=self.font_arrows,
            fg="#4caf50",
            bg='#2b2b2b',
            width=1
        )
        self.dl_arrow.pack(side=tk.LEFT)

        self.dl_text = tk.Label(
            self.dl_widget,
            text="0.0",
            font=self.font_speed,
            fg="#e0e0e0",
            bg='#2b2b2b',
            width=5,
            anchor='e'
        )
        self.dl_text.pack(side=tk.LEFT)

        self.dl_unit = tk.Label(
            self.dl_widget,
            text="MB",
            font=self.font_speed,
            fg="#909090",
            bg='#2b2b2b',
            width=2
        )
        self.dl_unit.pack(side=tk.LEFT)

        # Divider
        self.divider = tk.Frame(self.container, width=1, bg='#404040')
        self.divider.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=4)

        # Upload widget
        self.ul_widget = tk.Frame(self.container, bg='#2b2b2b', padx=6)
        self.ul_widget.pack(side=tk.LEFT, fill=tk.Y)

        self.ul_arrow = tk.Label(
            self.ul_widget,
            text="▲",
            font=self.font_arrows,
            fg="#2196f3",
            bg='#2b2b2b',
            width=1
        )
        self.ul_arrow.pack(side=tk.LEFT)

        self.ul_text = tk.Label(
            self.ul_widget,
            text="0.0",
            font=self.font_speed,
            fg="#e0e0e0",
            bg='#2b2b2b',
            width=5,
            anchor='e'
        )
        self.ul_text.pack(side=tk.LEFT)

        self.ul_unit = tk.Label(
            self.ul_widget,
            text="MB",
            font=self.font_speed,
            fg="#909090",
            bg='#2b2b2b',
            width=2
        )
        self.ul_unit.pack(side=tk.LEFT)

        # Bind mouse events for dragging and menu
        for widget in [self.container, self.dl_widget, self.ul_widget,
                       self.dl_arrow, self.dl_text, self.dl_unit,
                       self.ul_arrow, self.ul_text, self.ul_unit]:
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)
            widget.bind('<Button-3>', self.show_menu)
            widget.bind('<Double-Button-1>', self.cycle_position)

        # Drag variables
        self.drag_x = 0
        self.drag_y = 0
        self.pos_x = self.x
        self.pos_y = self.y

        # Menu
        self.menu = tk.Menu(
            self.root,
            tearoff=0,
            bg='#2b2b2b',
            fg='#ffffff',
            activebackground='#404040',
            activeforeground='#ffffff',
            font=('Segoe UI', 9)
        )
        self.menu.add_command(label="📍 Auto-dock to Taskbar", command=self.auto_dock)
        self.menu.add_separator()
        self.menu.add_command(label="⬇ Position: Bottom", command=lambda: self.set_position('bottom'))
        self.menu.add_command(label="⬆ Position: Top", command=lambda: self.set_position('top'))
        self.menu.add_command(label="➡ Position: Right", command=lambda: self.set_position('right'))
        self.menu.add_command(label="⬅ Position: Left", command=lambda: self.set_position('left'))
        self.menu.add_command(label="🔄 Position: Floating", command=lambda: self.set_position('float'))
        self.menu.add_separator()
        self.menu.add_command(label="❌ Exit", command=self.exit_app)

        # Network monitoring
        self.running = True
        net_io = psutil.net_io_counters()
        self.last_recv = net_io.bytes_recv
        self.last_sent = net_io.bytes_sent
        self.position = 'bottom'

        # Start monitoring
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def detect_taskbar_position(self):
        """Detect where the Windows taskbar is located"""
        # Simple heuristic - check where there's most empty space
        # In a real app, you'd use Windows API (SHAppBarMessage)
        # Default assumption: taskbar at bottom
        return 'bottom'

    def calculate_position(self):
        """Calculate default position based on taskbar"""
        # Place near system tray area (bottom-right)
        x = self.screen_width - self.width - 100
        y = self.screen_height - self.height - 45  # Just above typical taskbar
        return x, y

    def set_position(self, pos):
        """Set widget position"""
        self.position = pos

        if pos == 'bottom':
            self.x = self.screen_width - self.width - 100
            self.y = self.screen_height - self.height - 45
        elif pos == 'top':
            self.x = self.screen_width - self.width - 100
            self.y = 0
        elif pos == 'right':
            self.x = self.screen_width - self.width
            self.y = self.screen_height // 2
        elif pos == 'left':
            self.x = 0
            self.y = self.screen_height // 2
        # 'float' - keep current position

        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

    def auto_dock(self):
        """Automatically dock to taskbar"""
        self.set_position('bottom')

    def cycle_position(self, event=None):
        """Cycle through positions on double-click"""
        positions = ['bottom', 'top', 'right', 'left', 'float']
        current_idx = positions.index(self.position) if self.position in positions else -1
        next_idx = (current_idx + 1) % len(positions)
        self.set_position(positions[next_idx])

    def start_drag(self, event):
        self.drag_x = event.x_root
        self.drag_y = event.y_root
        self.pos_x = self.x
        self.pos_y = self.y

    def on_drag(self, event):
        dx = event.x_root - self.drag_x
        dy = event.y_root - self.drag_y
        self.x = self.pos_x + dx
        self.y = self.pos_y + dy
        self.root.geometry(f"+{self.x}+{self.y}")
        self.position = 'float'

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def format_speed(self, bytes_per_sec):
        """Format speed with appropriate unit"""
        if bytes_per_sec >= 1024 * 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.1f}", "GB"
        elif bytes_per_sec >= 1024 * 1024:
            return f"{bytes_per_sec / (1024 * 1024):.1f}", "MB"
        elif bytes_per_sec >= 1024:
            return f"{bytes_per_sec / 1024:.0f}", "KB"
        else:
            return f"{bytes_per_sec:.0f}", " B"

    def update_display(self, dl_speed, ul_speed):
        """Update the display with new speeds"""
        dl_val, dl_unit = self.format_speed(dl_speed)
        ul_val, ul_unit = self.format_speed(ul_speed)

        self.dl_text.config(text=dl_val)
        self.dl_unit.config(text=dl_unit)
        self.ul_text.config(text=ul_val)
        self.ul_unit.config(text=ul_unit)

        # Update arrow colors based on activity
        if dl_speed > 1024 * 1024:
            self.dl_arrow.config(fg="#4caf50")  # Green
        elif dl_speed > 0:
            self.dl_arrow.config(fg="#81c784")  # Light green
        else:
            self.dl_arrow.config(fg="#666666")  # Gray

        if ul_speed > 1024 * 1024:
            self.ul_arrow.config(fg="#2196f3")  # Blue
        elif ul_speed > 0:
            self.ul_arrow.config(fg="#64b5f6")  # Light blue
        else:
            self.ul_arrow.config(fg="#666666")  # Gray

    def monitor_loop(self):
        """Monitor network speeds"""
        while self.running:
            net_io = psutil.net_io_counters()

            dl_speed = max(0, net_io.bytes_recv - self.last_recv)
            ul_speed = max(0, net_io.bytes_sent - self.last_sent)

            self.last_recv = net_io.bytes_recv
            self.last_sent = net_io.bytes_sent

            # Schedule GUI update
            self.root.after(0, lambda d=dl_speed, u=ul_speed: self.update_display(d, u))

            time.sleep(1)

    def exit_app(self):
        self.running = False
        self.root.destroy()
        sys.exit(0)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    print("Taskbar Embedded Speed Monitor")
    print("==============================")
    print("Widget will appear on your taskbar area")
    print("")
    print("Controls:")
    print("  • Drag to move")
    print("  • Right-click for menu")
    print("  • Double-click to cycle positions")
    print("")

    app = EmbeddedTaskbarMonitor()
    app.run()
