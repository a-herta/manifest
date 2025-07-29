"""Steam-related helper utilities."""

import os
import sys
from pathlib import Path
from typing import Optional

from ..core.config import Config

# Handle Windows-specific imports
try:
    import winreg

    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False


def find_steam_path() -> Optional[Path]:
    """Find Steam installation path from Windows registry.

    Returns:
        Path to Steam installation directory, or None if not found
    """
    # Only works on Windows
    if not HAS_WINREG or sys.platform != "win32":
        return None

    try:
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, Config.STEAM_REG_PATH)
        steam_path = Path(winreg.QueryValueEx(hkey, Config.STEAM_REG_KEY)[0])

        if Config.STEAM_EXE in os.listdir(steam_path):
            return steam_path

        return None
    except (FileNotFoundError, OSError):
        return None
