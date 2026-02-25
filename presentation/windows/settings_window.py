import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from typing import TYPE_CHECKING
import sys
import os

if TYPE_CHECKING:
    from application.services.configuration_service import ConfigurationService
    from presentation.widgets.taskbar_widget import TaskbarWidget
    from presentation.widgets.floating_widget import FloatingWidget


class SettingsWindow:
    def __init__(
        self,
        parent: tk.Tk,
        config_service: "ConfigurationService",
        active_widget: tk.Tk = None
    ) -> None:
        self.config_service = config_service
        self.config = config_service.config
        self.active_widget = active_widget

        self.window = tk.Toplevel(parent)
        self.window.title("Settings - Net Speed Meter")
        self.window.geometry("800x600")
        self.window.configure(bg="#2b2b2b")
        self.window.attributes("-topmost", True)

        self._setup_styles()
        self._build_ui()
        self._load_current_settings()

    def _setup_styles(self):
        style = ttk.Style(self.window)
        style.theme_use("clam")

        style.configure(
            "Header.TLabel",
            background="#1e88e5",
            foreground="white",
            font=("Segoe UI", 12, "bold"),
            padding=10
        )
        style.configure("Dark.TFrame", background="#2b2b2b")
        style.configure(
            "Setting.TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Settings.TCheckbutton",
            background="#2b2b2b",
            foreground="white"
        )

    def _build_ui(self):
        main_frame = ttk.Frame(self.window, style="Dark.TFrame", padding=10)
        main_frame.pack(fill="both", expand=True)

        # --- General Settings Section ---
        ttk.Label(main_frame, text="General Settings",
                  style="Header.TLabel").pack(fill="x", pady=(0, 10))

        gen_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        gen_frame.pack(fill="x", padx=20, pady=5)

        # Floating Widget Toggle
        self.var_floating = tk.BooleanVar()
        cb_floating = ttk.Checkbutton(
            gen_frame, text="Enable Floating Desktop Widget",
            variable=self.var_floating, style="Settings.TCheckbutton"
        )
        cb_floating.grid(row=0, column=0, sticky="w", pady=5)

        # Run at Startup Toggle
        self.var_startup = tk.BooleanVar()
        cb_startup = ttk.Checkbutton(
            gen_frame, text="Run at Windows Startup",
            variable=self.var_startup, style="Settings.TCheckbutton"
        )
        cb_startup.grid(row=0, column=1, sticky="w", padx=40, pady=5)

        # Font
        ttk.Label(gen_frame, text="Font Family:", style="Setting.TLabel").grid(
            row=1, column=0, sticky="w", pady=10)
        self.var_font = tk.StringVar()
        font_combo = ttk.Combobox(gen_frame, textvariable=self.var_font, values=[
                                  "Segoe UI", "Arial", "Consolas"])
        font_combo.grid(row=1, column=0, sticky="w", padx=(100, 0))

        ttk.Label(gen_frame, text="Font Size:", style="Setting.TLabel").grid(
            row=1, column=1, sticky="w", padx=40)
        self.var_size = tk.IntVar()
        ttk.Spinbox(gen_frame, from_=8, to=24, textvariable=self.var_size, width=5).grid(
            row=1, column=1, sticky="w", padx=(120, 0))

        # --- Colors Section ---
        ttk.Label(main_frame, text="Custom Theme Colors",
                  style="Header.TLabel").pack(fill="x", pady=(20, 10))

        color_frame = ttk.Frame(main_frame, style="Dark.TFrame")
        color_frame.pack(fill="x", padx=20)

        self.color_vars = {
            "bg_color": tk.StringVar(),
            "dl_color": tk.StringVar(),
            "ul_color": tk.StringVar(),
            "text_color": tk.StringVar()
        }

        self._add_color_picker(
            color_frame, "Background Color:", "bg_color", 0, 0)
        self._add_color_picker(
            color_frame, "Download Icon Color:", "dl_color", 1, 0)
        self._add_color_picker(
            color_frame, "Upload Icon Color:", "ul_color", 0, 1)
        self._add_color_picker(color_frame, "Text Color:", "text_color", 1, 1)

        # --- Footer Buttons ---
        btn_frame = ttk.Frame(self.window, style="Dark.TFrame")
        btn_frame.pack(side="bottom", fill="x", pady=20, padx=20)

        btn_apply = tk.Button(btn_frame, text="Apply Changes", bg="#2ecc71", fg="white", font=(
            "Segoe UI", 10, "bold"), bd=0, px=20, py=8, command=self._apply_changes)
        btn_apply.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text="Close", bg="#e74c3c", fg="white", font=(
            "Segoe UI", 10, "bold"), bd=0, px=20, py=8, command=self.window.destroy)
        btn_close.pack(side="right", padx=5)

    def _add_color_picker(self, parent, label_text, var_name, row, col):
        frame = ttk.Frame(parent, style="Dark.TFrame")
        frame.grid(row=row, column=col, padx=20, pady=10, sticky="w")

        ttk.Label(frame, text=label_text, style="Setting.TLabel").pack(
            side="left", padx=(0, 10))

        btn = tk.Button(
            frame, textvariable=self.color_vars[var_name], width=10, bd=1, relief="solid")
        btn.configure(command=lambda: self._choose_color(var_name, btn))
        btn.pack(side="left")

    def _choose_color(self, var_name, button):
        current_color = self.color_vars[var_name].get()
        color = colorchooser.askcolor(
            initialcolor=current_color, title=f"Choose {var_name}")
        if color[1]:  # user didn't cancel
            self.color_vars[var_name].set(color[1])
            button.configure(bg=color[1])
            # calculate contrasting text color for the button
            button.configure(fg="black" if self._get_brightness(
                color[1]) > 128 else "white")

    def _get_brightness(self, hex_color):
        h = hex_color.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return (r * 299 + g * 587 + b * 114) / 1000

    def _load_current_settings(self):
        self.var_floating.set(self.config.is_floating)
        self.var_startup.set(self.config.run_on_startup)
        self.var_font.set(self.config.font_family)
        self.var_size.set(self.config.font_size)

        for k, v in self.color_vars.items():
            val = getattr(self.config, k)
            v.set(val)

    def _apply_changes(self):
        # 1. Update Config Object
        self.config.is_floating = self.var_floating.get()
        self.config.run_on_startup = self.var_startup.get()
        self.config.font_family = self.var_font.get()
        self.config.font_size = self.var_size.get()

        for k, v in self.color_vars.items():
            setattr(self.config, k, v.get())

        # 2. Save to Disk
        self.config_service.save()

        # 3. Handle Startup Registry
        from infrastructure.system.startup_manager import StartupManager
        if self.config.run_on_startup:
            StartupManager.enable_startup()
        else:
            StartupManager.disable_startup()

        messagebox.showinfo(
            "Settings Saved",
            "Settings have been saved.\nRestarting application to apply display changes."
        )

        # 4. Hard restart the python process to reload widget
        os.execl(sys.executable, sys.executable, *sys.argv)
