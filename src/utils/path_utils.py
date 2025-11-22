import sys
from pathlib import Path
from typing import Union


def get_asset_path(relative_path: Union[str, Path]) -> str:
    """
    Return correct path for assets when running as:
    ✅ source code (Linux/macOS/Windows)
    ✅ PyInstaller Windows EXE (uses sys._MEIPASS)
    """

    # Use getattr to avoid static type checker warnings
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))

    return str(base_path / relative_path)
