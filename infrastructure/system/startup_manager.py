import winreg
import sys
import os
from pathlib import Path


class StartupManager:
    """Manages adding or removing the application from Windows Startup."""

    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "NetSpeedMeterPlus"

    @classmethod
    def enable_startup(cls) -> bool:
        """Adds the application to the Windows startup registry key."""
        try:
            exe_path = cls._get_executable_path()
            if not exe_path:
                return False

            # Add quotes around the path to handle spaces
            command = f'"{exe_path}"'

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, command)
            return True
        except Exception as e:
            print(f"Error enabling startup: {e}")
            return False

    @classmethod
    def disable_startup(cls) -> bool:
        """Removes the application from the Windows startup registry key."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, cls.APP_NAME)
            return True
        except FileNotFoundError:
            # Already removed
            return True
        except Exception as e:
            print(f"Error disabling startup: {e}")
            return False

    @classmethod
    def is_startup_enabled(cls) -> bool:
        """Checks if the application is currently in the startup registry key."""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_PATH,
                0,
                winreg.KEY_READ
            ) as key:
                value, _ = winreg.QueryValueEx(key, cls.APP_NAME)
                return bool(value)
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error checking startup status: {e}")
            return False

    @staticmethod
    def _get_executable_path() -> str:
        """
        Gets the path to the executable. 
        If running from source, returns the path to python.exe and main.py.
        If frozen (PyInstaller), returns the path to the standalone .exe.
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a sys.frozen attribute
            return sys.executable
        else:
            # Running from source python script
            # NOTE: For production distribution, it is recommended to use Pyinstaller.
            # Adding python.exe main.py to registry can be fragile if paths change.
            main_script = Path(sys.argv[0]).resolve()
            if not main_script.exists():
                # Fallback if somehow sys.argv[0] is messed up
                main_script = Path.cwd() / "main.py"

            python_exe = sys.executable
            # We construct a command that launches pythonw (no console) with the script
            # But since we are relying on python, let's use the current executable
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not Path(pythonw_exe).exists():
                pythonw_exe = python_exe

            return f"{pythonw_exe} {main_script}"
