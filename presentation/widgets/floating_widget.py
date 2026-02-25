import tkinter as tk
from typing import TYPE_CHECKING
import pystray
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from application.services.speed_monitor_service import SpeedMonitorService
    from infrastructure.database.sqlite_usage_repository import SqliteUsageRepository
    from application.services.configuration_service import ConfigurationService
    from domain.entities.network_usage import SpeedSnapshot


class FloatingWidget:
    """A floating, draggable speed monitor overlay."""

    WIDGET_WIDTH = 110
    WIDGET_HEIGHT = 40

    def __init__(
        self,
        service: "SpeedMonitorService",
        repo: "SqliteUsageRepository" = None,
        config_service: "ConfigurationService" = None
    ) -> None:
        self._service = service
        self._repo = repo
        self._config_service = config_service
        self.config = config_service.config if config_service else None

        self.bg_color = self.config.bg_color if self.config else "#010101"
        self.text_color = self.config.text_color if self.config else "#ffffff"
        self.ul_color = self.config.ul_color if self.config else "#f39c12"
        self.dl_color = self.config.dl_color if self.config else "#00e5ff"

        self.root = tk.Tk()
        self.root.title("SpeedMonitor_Floating")

        # Make frameless and transparent
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.9)
        self.root.configure(bg=self.bg_color)

        self.running = True
        self._tray_icon: pystray.Icon | None = None

        # Variables for dragging
        self._drag_start_x = 0
        self._drag_start_y = 0

        self._create_ui()
        self._setup_events()
        self._service.subscribe(self._on_speed)

    def _create_ui(self) -> None:
        self.root.geometry(f"{self.WIDGET_WIDTH}x{self.WIDGET_HEIGHT}+100+100")

        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill="both", expand=True)

        sys_font = ("Segoe UI Semibold", 10)
        if self.config:
            font_weight = "bold" if self.config.bold_font else "normal"
            sys_font = (self.config.font_family,
                        self.config.font_size, font_weight)

        icon_canvas = tk.Canvas(
            container, width=16, height=36,
            bg=self.bg_color, highlightthickness=0
        )
        icon_canvas.grid(row=0, column=0, rowspan=2, padx=(2, 6), pady=0)

        # Download (Top) - Cyan arrow pointing DOWN to a line
        icon_canvas.create_polygon(
            2, 7, 14, 7,      # Top flat part of the triangle
            8, 14,            # Pointing straight down
            fill=self.dl_color, width=0
        )
        icon_canvas.create_rectangle(
            5, 2, 11, 8, fill=self.dl_color, outline="")
        icon_canvas.create_rectangle(
            3, 16, 13, 17, fill=self.dl_color, outline="")

        # Upload (Bottom) - Orange arrow pointing UP from a line
        icon_canvas.create_rectangle(
            3, 20, 13, 21, fill=self.ul_color, outline="")
        icon_canvas.create_polygon(
            2, 30, 14, 30,    # Bottom flat part of the triangle
            8, 23,            # Pointing straight up
            fill=self.ul_color, width=0
        )
        icon_canvas.create_rectangle(
            5, 29, 11, 35, fill=self.ul_color, outline="")

        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=0, minsize=40)
        container.columnconfigure(2, weight=1)

        self.dl_num = tk.Label(
            container, text="0", font=sys_font,
            fg=self.text_color, bg=self.bg_color, anchor="e", bd=0, pady=0
        )
        self.dl_num.grid(row=0, column=1, sticky="e", pady=(0, 0), padx=(0, 2))
        self.dl_unit = tk.Label(
            container, text="B/s", font=sys_font,
            fg=self.text_color, bg=self.bg_color, anchor="w", bd=0, pady=0
        )
        self.dl_unit.grid(row=0, column=2, sticky="w", pady=(0, 0))

        self.ul_num = tk.Label(
            container, text="0", font=sys_font,
            fg=self.text_color, bg=self.bg_color, anchor="e", bd=0, pady=0
        )
        self.ul_num.grid(row=1, column=1, sticky="e", pady=(0, 0), padx=(0, 2))
        self.ul_unit = tk.Label(
            container, text="B/s", font=sys_font,
            fg=self.text_color, bg=self.bg_color, anchor="w", bd=0, pady=0
        )
        self.ul_unit.grid(row=1, column=2, sticky="w", pady=(0, 0))

        # Context menu
        self.menu = tk.Menu(
            self.root, tearoff=0, bg="#2b2b2b", fg="#ffffff",
            activebackground="#4d4d4d", activeforeground="#ffffff",
            font=("Segoe UI", 9), relief="flat", borderwidth=1
        )
        self.menu.add_command(label="Usage Statistics",
                              command=self._show_stats)
        self.menu.add_command(label="Network Adapters",
                              command=self._show_adapters)
        self.menu.add_command(label="Speed Converter",
                              command=self._show_converter)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.exit_app)

    def _setup_events(self) -> None:
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<Button-3>", self._show_menu)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_pointerx() - self._drag_start_x
        y = self.root.winfo_pointery() - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    def _show_menu(self, e: tk.Event) -> None:
        self.menu.post(e.x_root, e.y_root)

    def _show_stats(self) -> None:
        from presentation.windows.statistics_window import StatisticsWindow
        StatisticsWindow(self.root, self._service, self._repo)

    def _show_settings(self) -> None:
        from presentation.windows.settings_window import SettingsWindow
        SettingsWindow(self.root, self._config_service, self.root)

    def _show_adapters(self) -> None:
        from presentation.windows.adapter_config_window import AdapterConfigWindow
        AdapterConfigWindow(self.root, self._config_service)

    def _show_converter(self) -> None:
        from presentation.windows.speed_converter_window import SpeedConverterWindow
        SpeedConverterWindow(self.root)

    @staticmethod
    def _fmt(bps: int) -> tuple[str, str]:
        if bps >= 1024 ** 3:
            return f"{bps / 1024**3:.2f}", "GB/s"
        if bps >= 1024 ** 2:
            return f"{bps / 1024**2:.2f}", "MB/s"
        if bps >= 1024:
            return f"{bps / 1024:.2f}", "KB/s"
        return f"{bps:.0f}", "B/s"

    def _on_speed(self, snap: "SpeedSnapshot") -> None:
        try:
            self.root.after(0, self._update_labels, snap)
        except Exception:
            pass

    def _update_labels(self, snap: "SpeedSnapshot") -> None:
        try:
            ul_n, ul_u = self._fmt(snap.up_speed)
            dl_n, dl_u = self._fmt(snap.down_speed)
            self.ul_num.config(text=ul_n)
            self.ul_unit.config(text=ul_u)
            self.dl_num.config(text=dl_n)
            self.dl_unit.config(text=dl_u)
        except tk.TclError:
            pass

    def _create_tray_icon(self) -> Image.Image:
        img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.polygon([(32, 10), (54, 30), (10, 30)], fill=(0, 229, 255, 255))
        d.polygon([(32, 54), (54, 34), (10, 34)], fill=(243, 156, 18, 255))
        return img

    def _setup_tray(self) -> None:
        icon_img = self._create_tray_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Usage Statistics", self._tray_show_stats),
            pystray.MenuItem("Network Adapters", self._tray_show_adapters),
            pystray.MenuItem("Speed Converter", self._tray_show_converter),
            pystray.MenuItem("Settings", self._tray_show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._tray_exit),
        )
        self._tray_icon = pystray.Icon(
            "SpeedMonitor", icon_img, "Speed Monitor", menu)
        self._tray_icon.run()

    def _tray_show_stats(self, icon, item) -> None:
        self.root.after(0, self._show_stats)

    def _tray_show_adapters(self, icon, item) -> None:
        self.root.after(0, self._show_adapters)

    def _tray_show_converter(self, icon, item) -> None:
        self.root.after(0, self._show_converter)

    def _tray_show_settings(self, icon, item) -> None:
        self.root.after(0, self._show_settings)

    def _tray_exit(self, icon, item) -> None:
        self.root.after(0, self.exit_app)

    def run(self) -> None:
        import threading
        tray_thread = threading.Thread(target=self._setup_tray, daemon=True)
        tray_thread.start()
        self.root.mainloop()

    def exit_app(self) -> None:
        self.running = False
        self._service.unsubscribe(self._on_speed)
        if self._tray_icon:
            self._tray_icon.stop()
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass
