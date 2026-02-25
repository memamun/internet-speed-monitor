import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from infrastructure.system.adapter_provider import AdapterProvider
from application.services.configuration_service import ConfigurationService

BG_SURFACE = "#1a1a1a"
BG_CARD = "#222222"
ACCENT_MAIN = "#7c6af7"
ACCENT_UP = "#f39c12"
ACCENT_DN = "#00e5ff"


class AdapterConfigWindow:
    """Window allowing users to review system adapters and lock monitoring to a specific one."""

    def __init__(self, parent: tk.Tk, config_service: ConfigurationService) -> None:
        self._config_service = config_service
        self.config = config_service.config

        self._win = ctk.CTkToplevel(parent)
        self._win.title("Network Adapters")
        self._win.geometry("600x400")
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)
        self._win.configure(fg_color=BG_SURFACE)

        # Center on screen
        self._win.update_idletasks()
        x = (self._win.winfo_screenwidth() - 600) // 2
        y = (self._win.winfo_screenheight() - 400) // 2
        self._win.geometry(f"+{x}+{y}")

        # Load adapters
        self._adapters = AdapterProvider.get_interfaces()

        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self._win, height=60,
                              corner_radius=0, fg_color=BG_SURFACE)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = ctk.CTkLabel(header, text="Network Interface Configuration",
                             font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Description
        desc = ctk.CTkLabel(
            self._win,
            text="Select an adapter to restrict monitoring. Select 'All' to monitor global traffic.",
            font=ctk.CTkFont(size=12), text_color="gray"
        )
        desc.pack(anchor="w", padx=20, pady=(0, 10))

        # Dropdown selection
        select_frame = ctk.CTkFrame(self._win, fg_color="transparent")
        select_frame.pack(fill=tk.X, padx=20, pady=10)

        ctk.CTkLabel(select_frame, text="Monitored Interface: ",
                     font=ctk.CTkFont(weight="bold")).pack(side=tk.LEFT)

        self.var_selected = tk.StringVar(value=getattr(
            self.config, 'monitored_adapter', 'All'))

        options = ["All"] + list(self._adapters.keys())
        # Ensure the currently saved option is in the list, even if disconnected
        if self.var_selected.get() not in options:
            options.append(self.var_selected.get())

        combo = ctk.CTkOptionMenu(
            select_frame, values=options, variable=self.var_selected,
            width=250, command=self._on_select
        )
        combo.pack(side=tk.LEFT, padx=10)

        # Treeview Scrollbar & Data
        tree_frame = ctk.CTkFrame(self._win, fg_color="transparent")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

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

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="none",
            columns=("Name", "Status", "Speed", "MAC"),
            show="headings"
        )
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self._tree.yview)

        self._tree.heading("Name", text="Network Adapter")
        self._tree.column("Name", anchor=tk.W, width=150)

        self._tree.heading("Status", text="Status")
        self._tree.column("Status", anchor=tk.W, width=60)

        self._tree.heading("Speed", text="Speed (MBps)")
        self._tree.column("Speed", anchor=tk.E, width=80)

        self._tree.heading("MAC", text="MAC Address")
        self._tree.column("MAC", anchor=tk.W, width=120)

        self._populate_tree()

        # Footer
        footer = ctk.CTkFrame(self._win, height=60,
                              corner_radius=0, fg_color="transparent")
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))
        footer.pack_propagate(False)

        btn_close = ctk.CTkButton(
            footer, text="Done", width=100,
            fg_color=ACCENT_MAIN, hover_color="#9b8df9",
            command=self._win.destroy
        )
        btn_close.pack(side=tk.RIGHT, padx=20)

    def _populate_tree(self) -> None:
        for name, data in self._adapters.items():
            status = "Connected" if data["isup"] else "Offline"
            speed = data["speed"] if data["speed"] > 0 else "N/A"
            mac = data["mac"] if data["mac"] else "Unknown"

            self._tree.insert(
                "", tk.END,
                values=(name, status, speed, mac)
            )

    def _on_select(self, choice: str) -> None:
        # Dynamically add the 'monitored_adapter' property to the config dict/object to save it
        if choice == "All":
            self.config.monitored_adapter = "All"
        else:
            self.config.monitored_adapter = choice

        self._config_service.save()
