#!/usr/bin/env bash
set -e

echo "📦 Commanders' Arena - Automatic Setup"
echo "---------------------------------------"

# -------------------------------
# 1. Python version check
# -------------------------------
echo "🔍 Checking Python version..."
python3 --version || { echo "❌ Python3 is not installed."; exit 1; }

PYV=$(python3 - <<'EOF'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
EOF
)

if [[ "$PYV" < "3.11" ]]; then
    echo "❌ Python 3.11+ required. Current: $PYV"
    exit 1
fi

echo "✔ Python $PYV OK"

# -------------------------------
# 2. Install Poetry if missing
# -------------------------------
if ! command -v poetry >/dev/null 2>&1 ; then
    echo "📥 Poetry not found — installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✔ Poetry found"
fi

# -------------------------------
# 3. Force Poetry to use project-local .venv
# -------------------------------
echo "🔧 Configuring Poetry to create virtualenv inside project..."
poetry config virtualenvs.in-project true

# -------------------------------
# 4. Install dependencies
# -------------------------------
echo "📦 Installing project dependencies via Poetry..."
poetry install

echo ""
echo "🎉 Setup complete!"
echo "👉 Start the game using:  poetry run game"
