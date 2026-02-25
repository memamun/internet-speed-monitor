from dataclasses import dataclass


@dataclass
class AppConfig:
    """Stores user preferences for the application."""
    is_floating: bool = False

    font_family: str = "Segoe UI"
    font_size: int = 10
    bold_font: bool = True

    # Colors
    bg_color: str = "#010101"
    dl_color: str = "#00e5ff"  # Cyan
    ul_color: str = "#f39c12"  # Orange
    text_color: str = "#ffffff"

    # Startup behavior
    run_on_startup: bool = False

    # Advanced Monitor Settings
    monitored_adapter: str = "All"

    def to_dict(self) -> dict:
        return {
            "is_floating": self.is_floating,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bold_font": self.bold_font,
            "bg_color": self.bg_color,
            "dl_color": self.dl_color,
            "ul_color": self.ul_color,
            "text_color": self.text_color,
            "run_on_startup": self.run_on_startup,
            "monitored_adapter": self.monitored_adapter
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            is_floating=data.get("is_floating", False),
            font_family=data.get("font_family", "Segoe UI"),
            font_size=data.get("font_size", 10),
            bold_font=data.get("bold_font", True),
            bg_color=data.get("bg_color", "#010101"),
            dl_color=data.get("dl_color", "#00e5ff"),
            ul_color=data.get("ul_color", "#f39c12"),
            text_color=data.get("text_color", "#ffffff"),
            run_on_startup=data.get("run_on_startup", False),
            monitored_adapter=data.get("monitored_adapter", "All")
        )
