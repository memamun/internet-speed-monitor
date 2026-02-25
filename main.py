#!/usr/bin/env python3
"""SpeedMonitor — Entry Point.

Bootstraps the layered architecture:
  Infrastructure → Application → Presentation
"""

import sys
import ctypes
from pathlib import Path

# Ensure project root is on sys.path (for package imports)
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from application.services.speed_monitor_service import SpeedMonitorService  # noqa: E402
from infrastructure.database.sqlite_usage_repository import \
    SqliteUsageRepository  # noqa: E402
from infrastructure.system.network_provider import NetworkProvider  # noqa: E402
from presentation.widgets.taskbar_widget import TaskbarWidget  # noqa: E402


def main() -> None:
    # Mutex for Inno Setup (CloseApplications detection)
    mutex_name = "SpeedMonitorMutex"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    
    # 183 = ERROR_ALREADY_EXISTS
    if last_error == 183:
        print("SpeedMonitor is already running.")
        sys.exit(0)

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
