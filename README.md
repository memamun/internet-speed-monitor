# Internet Speed Monitor

A lightweight desktop app that displays real-time internet upload and download speeds on Windows, similar to DU Meter.

## Two Display Modes

### Option 1: System Tray Icon
Traditional icon in the system tray (notification area).

**Best for:** Minimal desktop footprint

**Looks like:** ▼ 1.5M / ▲ 200K

### Option 2: Taskbar Widget ⭐ Recommended
A floating widget that sits ON the taskbar showing live speed text.

**Best for:** Always-visible speeds like DU Meter

**Looks like:** ▼ 1.5 MB ▲ 200 KB

## Features

- **Real-time monitoring** - Updates every second
- **Upload & Download speeds** - Shows both directions
- **Two display modes** - System tray or taskbar widget
- **Drag to position** - Place anywhere you want
- **Auto-dock options** - Bottom, top, left, right taskbar
- **Color-coded** - Green for download, blue for upload
- **Right-click menu** - Quick settings and exit
- **Always on top** - Stays visible over other windows

## Requirements

- Windows 10/11
- Python 3.7 or higher

## Installation

1. **Install Python** (if not already installed)
   - Download from: https://python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Install dependencies**
   ```batch
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```batch
   run.bat
   ```
   Then choose:
   - `1` for System Tray Icon
   - `2` for Taskbar Widget

## Usage

### Taskbar Widget (Recommended)

This is what you want if you want to see speeds like DU Meter directly on your taskbar.

**Controls:**
- **Drag** the widget to position it anywhere
- **Right-click** for menu (dock positions, exit)
- **Double-click** to cycle through dock positions

**Dock positions available:**
- Bottom (default) - sits on top of taskbar
- Top - above screen
- Left/Right - screen edges
- Floating - anywhere you drag

### System Tray Icon

- Look for the icon near your clock
- **Hover** over the icon to see speeds
- **Right-click** the icon for menu

## Files

| File | Description |
|------|-------------|
| `speed_monitor.py` | System tray icon version |
| `taskbar_speed_monitor.py` | Simple taskbar widget |
| `taskbar_embedded.py` | Better taskbar widget (recommended) |
| `run.bat` | Easy launcher |

## Run Individual Versions

```batch
# System tray icon
python speed_monitor.py

# Simple taskbar widget
python taskbar_speed_monitor.py

# Better taskbar widget (recommended)
python taskbar_embedded.py
```

## Creating an Executable (Optional)

To create a standalone `.exe` file that doesn't require Python:

1. Install PyInstaller:
   ```batch
   pip install pyinstaller
   ```

2. Build the taskbar widget:
   ```batch
   pyinstaller --onefile --windowed --name "NetSpeed" taskbar_embedded.py
   ```

3. Find the executable in the `dist` folder

## Auto-start with Windows (Optional)

### Method 1: Startup Folder
1. Press `Win + R` and type `shell:startup`
2. Create a shortcut to `run.bat` or the `.exe`
3. Place the shortcut in the Startup folder

### Method 2: Task Scheduler
1. Open Task Scheduler
2. Create new task, set trigger to "At log on"
3. Action: Start `pythonw.exe` with argument `taskbar_embedded.py`
4. Set "Run whether user is logged on or not"

## Troubleshooting

### Widget not visible?
- Make sure it's not behind another window
- Try running as administrator
- Check if antivirus is blocking it

### Wrong position after screen changes?
- Right-click → "Auto-dock to Taskbar" to reset position

### Speed showing 0?
- Check your network connection
- The widget measures ALL network traffic on your PC

## Uninstall

Simply delete the application folder. No registry entries or system files are modified.

## License

MIT License - Free to use and modify
