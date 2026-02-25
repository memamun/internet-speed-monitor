#!/usr/bin/env python3
"""
Real-time Internet Speed Monitor for Windows Taskbar
Similar to DU Meter - shows upload/download speeds in system tray
"""

import threading
import time
import psutil
import pystray
from PIL import Image, ImageDraw, ImageFont


class SpeedMonitor:
    def __init__(self):
        self.upload_speed = 0.0
        self.download_speed = 0.0
        self.last_bytes_sent = 0
        self.last_bytes_recv = 0
        self.running = True
        self.icon = None
        self.update_interval = 1.0  # Update every second

        # Initialize network counters
        net_io = psutil.net_io_counters()
        self.last_bytes_sent = net_io.bytes_sent
        self.last_bytes_recv = net_io.bytes_recv

    def format_speed(self, speed_bytes):
        """Convert bytes/s to human readable format"""
        if speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.1f} MB/s"
        elif speed_bytes >= 1024:
            return f"{speed_bytes / 1024:.1f} KB/s"
        else:
            return f"{speed_bytes:.0f} B/s"

    def format_speed_short(self, speed_bytes):
        """Short format for icon label (e.g., '1.5M' or '500K')"""
        if speed_bytes >= 1024 * 1024:
            return f"{speed_bytes / (1024 * 1024):.1f}M"
        elif speed_bytes >= 1024:
            return f"{speed_bytes / 1024:.0f}K"
        elif speed_bytes > 0:
            return f"{speed_bytes:.0f}"
        else:
            return "0"

    def create_icon_image(self):
        """Create a simple icon showing up/down arrows with speeds"""
        # Create a 64x64 image with transparent background
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Try to load a font, fallback to default if not available
        try:
            font_small = ImageFont.truetype("segoeui.ttf", 10)
            font_large = ImageFont.truetype("segoeui.ttf", 12)
        except:
            font_small = ImageFont.load_default()
            font_large = ImageFont.load_default()

        # Background (semi-transparent black)
        draw.rectangle([0, 0, width, height], fill=(30, 30, 30, 220), outline=(100, 100, 100, 255), width=1)

        # Download section (top half - green)
        dl_text = self.format_speed_short(self.download_speed)
        draw.rectangle([2, 2, width-2, height//2 - 1], fill=(0, 150, 0, 200))
        draw.text((width//2, height//4), "▼", fill=(255, 255, 255, 255), font=font_large, anchor="mm")
        draw.text((width//2, height//4 + 12), dl_text, fill=(255, 255, 255, 255), font=font_small, anchor="mm")

        # Upload section (bottom half - blue)
        ul_text = self.format_speed_short(self.upload_speed)
        draw.rectangle([2, height//2, width-2, height-2], fill=(0, 100, 200, 200))
        draw.text((width//2, 3*height//4), "▲", fill=(255, 255, 255, 255), font=font_large, anchor="mm")
        draw.text((width//2, 3*height//4 + 12), ul_text, fill=(255, 255, 255, 255), font=font_small, anchor="mm")

        return image

    def update_speeds(self):
        """Calculate current upload/download speeds"""
        net_io = psutil.net_io_counters()

        # Calculate speeds
        self.download_speed = max(0, net_io.bytes_recv - self.last_bytes_recv)
        self.upload_speed = max(0, net_io.bytes_sent - self.last_bytes_sent)

        # Update last values
        self.last_bytes_recv = net_io.bytes_recv
        self.last_bytes_sent = net_io.bytes_sent

    def update_tray_icon(self):
        """Update the system tray icon with current speeds"""
        if self.icon:
            # Update the icon image
            self.icon.icon = self.create_icon_image()
            # Update tooltip
            tooltip = f"Download: {self.format_speed(self.download_speed)}\nUpload: {self.format_speed(self.upload_speed)}"
            self.icon.title = tooltip

    def monitor_loop(self):
        """Background thread for monitoring network speed"""
        while self.running:
            self.update_speeds()
            self.update_tray_icon()
            time.sleep(self.update_interval)

    def create_menu(self):
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem(
                lambda text: f"Download: {self.format_speed(self.download_speed)}",
                lambda icon, item: None,
                enabled=False
            ),
            pystray.MenuItem(
                lambda text: f"Upload: {self.format_speed(self.upload_speed)}",
                lambda icon, item: None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_action)
        )

    def exit_action(self, icon, item):
        """Exit the application"""
        self.running = False
        icon.stop()

    def run(self):
        """Start the speed monitor"""
        # Create initial icon
        initial_icon = self.create_icon_image()

        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()

        # Create system tray icon
        self.icon = pystray.Icon(
            "speed_monitor",
            initial_icon,
            "Internet Speed Monitor\nStarting...",
            menu=self.create_menu()
        )

        # Update menu periodically
        def update_menu():
            while self.running:
                self.icon.menu = self.create_menu()
                time.sleep(1)

        menu_thread = threading.Thread(target=update_menu, daemon=True)
        menu_thread.start()

        # Run the system tray icon
        self.icon.run()


if __name__ == "__main__":
    print("Starting Internet Speed Monitor...")
    print("Look for the icon in your system tray (near the clock)")
    print("Right-click the icon to see speeds or exit")

    app = SpeedMonitor()
    app.run()
