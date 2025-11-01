# utils/path_utils.py

import sys
from pathlib import Path
from typing import Union


def get_asset_path(relative_path: Union[str, Path]) -> str:
    """
    Return correct path for assets when running as:
    ✅ source code (Linux/macOS/Windows)
    ✅ PyInstaller Windows EXE (uses sys._MEIPASS)
    """

    # PyInstaller adds sys._MEIPASS at runtime
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)

    return str(Path(base_path) / relative_path)
