import json
import os
from pathlib import Path
from domain.entities.configuration import AppConfig


class ConfigurationService:
    """Manages loading and saving application configuration."""

    def __init__(self, app_data_dir: str = None) -> None:
        if app_data_dir:
            self._dir = Path(app_data_dir)
        else:
            self._dir = Path(os.environ.get(
                "LOCALAPPDATA", "")) / "SpeedMonitor"

        self._dir.mkdir(parents=True, exist_ok=True)
        self._config_file = self._dir / "config.json"

        self.config = self.load()

    def load(self) -> AppConfig:
        """Load configuration from disk, or return default if missing/invalid."""
        if not self._config_file.exists():
            return AppConfig()

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig.from_dict(data)
        except Exception as e:
            print(f"Error loading config: {e}")
            return AppConfig()

    def save(self) -> None:
        """Persist current configuration to disk."""
        try:
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
