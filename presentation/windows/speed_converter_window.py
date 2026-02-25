import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import math

# Use the same aesthetics as Statistics
BG_SURFACE = "#1a1a1a"
BG_CARD = "#222222"
ACCENT_UP = "#f39c12"
ACCENT_DN = "#00e5ff"
ACCENT_MAIN = "#7c6af7"


class SpeedConverterWindow:
    """A standalone calculator to convert between bits, bytes, and network speeds."""

    def __init__(self, parent: tk.Tk) -> None:
        self._win = ctk.CTkToplevel(parent)
        self._win.title("Speed Converter")
        self._win.geometry("450x300")
        self._win.resizable(False, False)
        self._win.attributes("-topmost", True)
        self._win.configure(fg_color=BG_SURFACE)

        # Center on screen
        self._win.update_idletasks()
        x = (self._win.winfo_screenwidth() - 450) // 2
        y = (self._win.winfo_screenheight() - 300) // 2
        self._win.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self._win, height=60,
                              corner_radius=0, fg_color=BG_SURFACE)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = ctk.CTkLabel(header, text="Network Speed Converter",
                             font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(side=tk.LEFT, padx=20, pady=15)

        # Main Card
        card = ctk.CTkFrame(self._win, corner_radius=8, fg_color=BG_CARD)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Input Row
        self.var_input = tk.StringVar(value="1")
        self.var_input.trace_add("write", self._calculate)

        inp_scale = ctk.CTkEntry(
            card, textvariable=self.var_input,
            width=150, font=ctk.CTkFont(size=14)
        )
        inp_scale.grid(row=0, column=0, padx=(
            20, 10), pady=(30, 0), sticky="w")

        self.var_unit = tk.StringVar(value="Mbps")
        units = ["Kbps", "Mbps", "Gbps", "KB/s", "MB/s", "GB/s"]
        unit_combo = ctk.CTkOptionMenu(
            card, values=units, variable=self.var_unit,
            command=self._calculate, width=100
        )
        unit_combo.grid(row=0, column=1, padx=(
            0, 20), pady=(30, 0), sticky="w")

        # Results Label
        self.lbl_result1 = ctk.CTkLabel(
            card, text="= 0.125 MB/s", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_DN)
        self.lbl_result1.grid(row=1, column=0, columnspan=2,
                              padx=20, pady=(30, 5), sticky="w")

        self.lbl_result2 = ctk.CTkLabel(
            card, text="= 125 KB/s", font=ctk.CTkFont(size=14), text_color="gray")
        self.lbl_result2.grid(row=2, column=0, columnspan=2,
                              padx=20, pady=(0, 20), sticky="w")

        self._calculate()

    def _calculate(self, *args) -> None:
        try:
            val = float(self.var_input.get() or "0")
        except ValueError:
            self.lbl_result1.configure(text="Invalid Input")
            self.lbl_result2.configure(text="")
            return

        unit = self.var_unit.get()

        # 1. Convert everything to raw bits per second (bps)
        bps = 0
        if unit == "Kbps":
            bps = val * 1000
        elif unit == "Mbps":
            bps = val * 1000 * 1000
        elif unit == "Gbps":
            bps = val * 1000 * 1000 * 1000
        elif unit == "KB/s":
            bps = val * 1024 * 8
        elif unit == "MB/s":
            bps = val * 1024 * 1024 * 8
        elif unit == "GB/s":
            bps = val * 1024 * 1024 * 1024 * 8

        # 2. Output the mathematical complement
        # If input was bits (b), output Bytes (B) and vice versa.
        bytes_per_sec = bps / 8

        if "b" in unit:  # Network Speeds (Mbps) -> File Sizes (MB/s)
            mb = bytes_per_sec / (1024 * 1024)
            kb = bytes_per_sec / 1024
            self.lbl_result1.configure(text=f"= {mb:,.3f} MB/s")
            self.lbl_result2.configure(text=f"= {kb:,.2f} KB/s")
        else:  # File Sizes (MB/s) -> Network Speeds (Mbps)
            mbps = bps / (1000 * 1000)
            kbps = bps / 1000
            self.lbl_result1.configure(text=f"= {mbps:,.2f} Mbps")
            self.lbl_result2.configure(text=f"= {kbps:,.2f} Kbps")
