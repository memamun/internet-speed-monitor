@echo off
chcp 65001 >nul
echo =========================================
echo    Internet Speed Monitor
echo =========================================
echo.
echo Choose display mode:
echo 1. System Tray Icon (near clock)
echo 2. Taskbar Widget (floating text on taskbar)
echo 3. Taskbar Embedded (TrafficMonitor-style)
echo.
set /p choice="Enter choice (1, 2, or 3): "

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check if required packages are installed
echo.
echo Checking dependencies...
python -c "import psutil, pystray, PIL" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

if "%choice%"=="1" (
    echo.
    echo Starting System Tray Speed Monitor...
    echo Look for the icon in your system tray (near the clock)
    echo Right-click the icon to see speeds or exit
echo.
    python speed_monitor.py
) else if "%choice%"=="2" (
    echo.
    echo Starting Taskbar Widget Speed Monitor...
    echo A floating widget will appear. Drag to position on taskbar.
    echo Right-click the widget for menu options.
    echo.
    echo Close this window to exit.
    echo.
    python taskbar_speed_monitor.py
) else if "%choice%"=="3" (
    echo.
    echo Starting Taskbar Embedded Speed Monitor...
    echo Widget will embed into Windows taskbar like TrafficMonitor.
    echo Right-click the widget for menu options.
    echo.
    python taskbar_widget.py
) else (
    echo Invalid choice. Exiting.
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ERROR: Application crashed
    pause
)
