# SpeedMonitor 📡

A lightweight Windows taskbar widget that displays real-time **upload & download speeds**, similar to DU Meter and TrafficMonitor. Built with Python, CustomTkinter, and psutil.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)](https://www.microsoft.com/windows)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)

![SpeedMonitor Screenshot](assets/preview.png)

---

## ✨ Features

- **📡 Live Speed Display** — Real-time upload & download speeds, updated every second
- **🖥 Taskbar Embedding** — Embeds natively into the Windows taskbar (overlay fallback on newer Windows)
- **📊 Usage Statistics** — Daily, monthly, and 30-day trend charts with peak/avg speeds
- **🗄 Data Persistence** — SQLite database tracks daily usage history automatically
- **🔔 System Tray** — Tray icon with quick access menu
- **📈 Statistics Window** — Premium dark-themed UI with Today / This Month / Trends tabs
- **📤 CSV Export** — Export all historical usage data

---

## 🏗 Architecture

4-layer enterprise architecture for maintainability:

```
Domain      → Pure Python entities (DailyUsage, MonthlyUsage, SpeedSnapshot)
Application → SpeedMonitorService (pub/sub, accumulation, flush)
Infrastructure → SQLite repo, psutil NetworkProvider, Win32 Taskbar helper
Presentation → CustomTkinter StatisticsWindow, Tkinter TaskbarWidget
```

---

## 🚀 Quick Start

### Option A — PowerShell One-Liner ⭐ Easiest
```powershell
irm memamun.github.io/internet-speed-monitor/install.ps1 | iex
```
Downloads and silently installs the latest release automatically.

### Option B — Download Executable
1. Go to [**Releases**](https://github.com/memamun/internet-speed-monitor/releases/latest)
2. Download `SpeedMonitor_Setup_vX.X.X.exe`
3. Run it — no Python required!

### Option C — Run from Source
```powershell
pip install -r requirements.txt
python main.py
```

---

## 📋 Requirements (source)

| Package | Purpose |
|---|---|
| `psutil` | Network byte counters |
| `pystray` | System tray icon |
| `Pillow` | Tray icon image |
| `pywin32` | Win32 taskbar embedding |
| `customtkinter` | Statistics window UI |
| `matplotlib` | Trend charts |

---

## 💡 Usage

- **Right-click** the taskbar widget → context menu
- → **Usage Statistics** — opens the statistics window
- → **Exit** — closes the app

---

## 📁 Project Structure

```
internet-speed-monitor/
├── main.py                          # Entry point
├── domain/entities/                 # DailyUsage, MonthlyUsage, SpeedSnapshot
├── domain/interfaces/               # UsageRepository interface
├── application/services/            # SpeedMonitorService
├── infrastructure/database/         # SQLite repository
├── infrastructure/system/           # NetworkProvider, WindowsTaskbar
├── presentation/widgets/            # TaskbarWidget
├── presentation/windows/            # StatisticsWindow
└── requirements.txt
```

---

## 🪟 Windows Store

A Microsoft Store release is planned. The Store version will use overlay/floating mode since taskbar embedding requires elevated Win32 access not available in the Store sandbox.

---

## 📄 License

MIT License — free to use, modify and distribute.
