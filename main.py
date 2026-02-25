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

from infrastructure.database.sqlite_usage_repository import SqliteUsageRepository
from infrastructure.system.network_provider import NetworkProvider
from application.services.speed_monitor_service import SpeedMonitorService
from presentation.widgets.taskbar_widget import TaskbarWidget


def main() -> None:
    print()
    print("SpeedMonitor")
    print("=" * 40)
    print("Right-click widget → Usage Statistics / Exit")
    print()

    # 1. Infrastructure
    repo = SqliteUsageRepository(db_dir=_ROOT)
    network = NetworkProvider()

    # 2. Application
    service = SpeedMonitorService(network=network, repo=repo)

    # 3. Presentation
    widget = TaskbarWidget(service=service, repo=repo)
    widget.run()


if __name__ == "__main__":
    main()
