#!/usr/bin/env python3
"""SpeedMonitor — Entry Point.

Bootstraps the layered architecture:
  Infrastructure → Application → Presentation
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path (for package imports)
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from application.services.speed_monitor_service import SpeedMonitorService  # noqa: E402
from application.services.configuration_service import ConfigurationService  # noqa: E402
from infrastructure.database.sqlite_usage_repository import \
    SqliteUsageRepository  # noqa: E402
from infrastructure.system.network_provider import NetworkProvider  # noqa: E402
from presentation.widgets.taskbar_widget import TaskbarWidget  # noqa: E402
from presentation.widgets.floating_widget import FloatingWidget  # noqa: E402


def main() -> None:
    print()
    print("SpeedMonitor")
    print("=" * 40)
    print("Right-click widget → Usage Statistics / Exit")
    print()

    # 1. Infrastructure
    config_service = ConfigurationService(app_data_dir=str(_ROOT))
    repo = SqliteUsageRepository(db_dir=_ROOT)
    network = NetworkProvider(config=config_service.config)

    # 2. Application
    service = SpeedMonitorService(network=network, repo=repo)

    # 3. Presentation
    # Always create the TaskbarWidget (it handles the tray icon and main window)
    taskbar = TaskbarWidget(service=service, repo=repo, config_service=config_service)
    widgets = [taskbar]

    # If floating is enabled, create it as a child of the taskbar root
    if config_service.config.is_floating:
        floating = FloatingWidget(
            service=service, repo=repo, config_service=config_service, parent=taskbar.root)
        widgets.append(floating)

    try:
        # Run the main taskbar widget
        taskbar.run()
    except Exception as e:
        print(f"Error starting widgets: {e}")

if __name__ == "__main__":
    main()
