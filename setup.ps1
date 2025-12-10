Write-Host "📦 Commanders' Arena - Automatic Setup"
Write-Host "---------------------------------------"

# -------------------------------
# 1. Python version check
# -------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed."
    exit 1
}

$pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"

$major, $minor = $pyv -split "\."

if ($major -lt 3 -or $minor -lt 11) {
    Write-Host "❌ Python 3.11+ required. Current: $pyv"
    exit 1
}

Write-Host "✔ Python $pyv OK"

# -------------------------------
# 2. Install Poetry if missing
# -------------------------------
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "📥 Poetry not found — installing..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

    # Add Poetry to PATH for this session
    $poetryPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts"
    if (-not ($env:PATH -like "*$poetryPath*")) {
        $env:PATH += ";$poetryPath"
    }
} else {
    Write-Host "✔ Poetry found"
}

# -------------------------------
# 3. Force Poetry to use .venv local environment
# -------------------------------
Write-Host "🔧 Configuring Poetry to create virtualenv inside project..."
poetry config virtualenvs.in-project true

# -------------------------------
# 4. Install dependencies
# -------------------------------
Write-Host "📦 Installing dependencies..."
poetry install

Write-Host "`n🎉 Setup complete!"
Write-Host "👉 Start the game using:  poetry run game"
