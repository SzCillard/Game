#!/usr/bin/env bash
set -e

echo "📦 Commanders' Arena - Automatic Setup"
echo "---------------------------------------"

# -------------------------------
# 1. Python version check
# -------------------------------
echo "🔍 Checking for Python 3.11..."

# Try python3.11 explicitly first (Ubuntu, Arch, Fedora)
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
else
    # Fallback to python3, but version must be exactly 3.11
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "❌ Python is not installed."
        echo "➡ Please install Python 3.11 manually."
        exit 1
    fi
fi

# Extract version
PYV=$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=${PYV%.*}
PY_MINOR=${PYV#*.}

# Enforce EXACT version
if [[ "$PY_MAJOR" -ne 3 || "$PY_MINOR" -ne 11 ]]; then
    echo "❌ Python 3.11 is required. Detected: $PYV"
    echo ""
    echo "📌 Install Python 3.11 using:"
    echo "  Ubuntu:  sudo apt install python3.11 python3.11-venv"
    echo "  Arch:    sudo pacman -S python311"
    echo "  Fedora:  sudo dnf install python3.11"
    echo ""
    exit 1
fi

echo "✔ Using Python: $PYTHON_BIN  (version $PYV)"

# Ensure pip exists for Python 3.11
if ! $PYTHON_BIN -m pip --version >/dev/null 2>&1; then
    echo "📥 Installing pip for Python 3.11..."
    $PYTHON_BIN -m ensurepip --upgrade
fi

# -------------------------------
# 2. Install Poetry if missing
# -------------------------------
if ! command -v poetry >/dev/null 2>&1; then
    echo "📥 Poetry not found — installing..."
    curl -sSL https://install.python-poetry.org | $PYTHON_BIN -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✔ Poetry found"
fi

# -------------------------------
# 3. Force project-local virtual environment
# -------------------------------
echo "🔧 Configuring Poetry to create .venv inside project..."
poetry config virtualenvs.in-project true

# -------------------------------
# 4. Install dependencies
# -------------------------------
echo "📦 Installing project dependencies via Poetry..."
poetry install

echo ""
echo "🎉 Setup complete!"
echo "👉 Start the game using:  poetry run game"
