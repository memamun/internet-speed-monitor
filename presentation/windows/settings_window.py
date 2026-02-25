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
        self.window.geometry("600x650")
        self.window.configure(bg="#121212")
        self.window.attributes("-topmost", True)

        # Remove default focus
        self.window.focus_force()

        # Define Colors
        self.bg_primary = "#121212"
        self.bg_card = "#1e1e1e"
        self.text_primary = "#ffffff"
        self.text_secondary = "#a0a0a0"
        self.accent_color = "#1e88e5"

        self._build_ui()
        self._load_current_settings()

    def _build_header(self, parent, text):
        lbl = tk.Label(parent, text=text, bg=self.bg_card, fg=self.text_primary,
                       font=("Segoe UI", 12, "bold"), anchor="w", padx=15, pady=10)
        lbl.pack(fill="x")
        # separator line
        tk.Frame(parent, bg="#333333", height=1).pack(fill="x")

    def _build_ui(self):
        # Container with padding
        main_container = tk.Frame(self.window, bg=self.bg_primary, padx=20, pady=20)
        main_container.pack(fill="both", expand=True)

        # Title
        tk.Label(
            main_container, text="Settings", bg=self.bg_primary, fg=self.text_primary,
            font=("Segoe UI", 20, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 20))

        # --- General Settings Card ---
        gen_card = tk.Frame(main_container, bg=self.bg_card, highlightbackground="#333333", highlightthickness=1)
        gen_card.pack(fill="x", pady=(0, 20))

        self._build_header(gen_card, "General")

        content_gen = tk.Frame(gen_card, bg=self.bg_card, padx=20, pady=15)
        content_gen.pack(fill="x")

        # Toggles
        toggle_frame = tk.Frame(content_gen, bg=self.bg_card)
        toggle_frame.pack(fill="x", pady=(0, 15))

        self.var_floating = tk.BooleanVar()
        tk.Checkbutton(
            toggle_frame, text="Enable Floating Desktop Widget", variable=self.var_floating,
            bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_primary,
            activebackground=self.bg_card, activeforeground=self.text_primary,
            font=("Segoe UI", 10)
        ).pack(side="left")

        self.var_startup = tk.BooleanVar()
        tk.Checkbutton(
            toggle_frame, text="Run at Windows Startup", variable=self.var_startup,
            bg=self.bg_card, fg=self.text_primary, selectcolor=self.bg_primary,
            activebackground=self.bg_card, activeforeground=self.text_primary,
            font=("Segoe UI", 10)
        ).pack(side="right")

        # Typography
        typo_frame = tk.Frame(content_gen, bg=self.bg_card)
        typo_frame.pack(fill="x")

        tk.Label(typo_frame, text="Font Family:", bg=self.bg_card, fg=self.text_secondary, font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.var_font = tk.StringVar()
        ttk.Combobox(typo_frame, textvariable=self.var_font, values=["Segoe UI", "Arial", "Consolas"], width=20).grid(row=0, column=1, sticky="w", padx=(0, 30))

        tk.Label(typo_frame, text="Font Size:", bg=self.bg_card, fg=self.text_secondary, font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", pady=5, padx=(0, 10))
        self.var_size = tk.IntVar()
        ttk.Spinbox(typo_frame, from_=8, to=24, textvariable=self.var_size, width=8).grid(row=0, column=3, sticky="w")

        # --- Colors Section Card ---
        color_card = tk.Frame(main_container, bg=self.bg_card, highlightbackground="#333333", highlightthickness=1)
        color_card.pack(fill="x", pady=(0, 20))

        self._build_header(color_card, "Appearance & Colors")

        content_color = tk.Frame(color_card, bg=self.bg_card, padx=20, pady=15)
        content_color.pack(fill="x")

        self.color_vars = {
            "bg_color": tk.StringVar(),
            "dl_color": tk.StringVar(),
            "ul_color": tk.StringVar(),
            "text_color": tk.StringVar()
        }

        # Grid for colors
        self._add_color_picker(content_color, "Background Color", "bg_color", 0, 0)
        self._add_color_picker(content_color, "Text Color", "text_color", 0, 1)
        self._add_color_picker(content_color, "Upload Icon Color", "ul_color", 1, 0)
        self._add_color_picker(content_color, "Download Icon Color", "dl_color", 1, 1)

        # --- Footer ---
        footer = tk.Frame(main_container, bg=self.bg_primary)
        footer.pack(fill="x", side="bottom")

        tk.Button(
            footer, text="Save & Apply", bg="#2ecc71", fg="#ffffff", font=("Segoe UI", 10, "bold"),
            bd=0, padx=20, pady=8, cursor="hand2", command=self._apply_changes
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            footer, text="Cancel", bg="#333333", fg="#ffffff", font=("Segoe UI", 10),
            bd=0, padx=20, pady=8, cursor="hand2", command=self.window.destroy
        ).pack(side="right")

    def _add_color_picker(self, parent, label_text, var_name, row, col):
        frame = tk.Frame(parent, bg=self.bg_card)
        frame.grid(row=row, column=col, sticky="w", pady=10, padx=(0, 40))

        tk.Label(frame, text=label_text, bg=self.bg_card, fg=self.text_secondary, font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        btn = tk.Button(frame, textvariable=self.color_vars[var_name], width=9, bd=0, font=("Consolas", 9))
        btn.configure(command=lambda: self._choose_color(var_name, btn))
        btn.pack(side="left")

    def _choose_color(self, var_name, button):
        current_color = self.color_vars[var_name].get()
        color = colorchooser.askcolor(initialcolor=current_color, title=f"Choose {var_name}")
        if color[1]:
            self.color_vars[var_name].set(color[1])
            self._update_btn_color(button, color[1])

    def _update_btn_color(self, button, hex_color):
        button.configure(bg=hex_color)
        button.configure(fg="#000000" if self._get_brightness(hex_color) > 128 else "#ffffff")

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
        
        # update button colors after init
        # Wait a small delay to ensure UI is drawn before finding buttons
        self.window.after(50, self._sync_button_colors)

    def _sync_button_colors(self):
        # A bit hacky, but iterates thru widgets to style the color buttons
        for w in self.window.winfo_children():
            self._recursively_sync_buttons(w)

    def _recursively_sync_buttons(self, widget):
        if isinstance(widget, tk.Button) and hasattr(widget, 'cget'):
            try:
                text_val = widget.cget('textvariable')
                if text_val:
                    for k, var in self.color_vars.items():
                        if str(var) == text_val:
                            self._update_btn_color(widget, var.get())
            except Exception:
                pass
        for child in widget.winfo_children():
            self._recursively_sync_buttons(child)

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

        self.window.destroy()
        messagebox.showinfo(
            "Settings Saved",
            "Settings have been saved.\nRestarting application to apply display changes."
        )

        # 4. Hard restart the python process to reload widget
        os.execl(sys.executable, sys.executable, *sys.argv)
