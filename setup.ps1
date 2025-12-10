Write-Host "Commanders' Arena - Automatic Setup"
Write-Host "---------------------------------------"

# -------------------------------
# 1. Python version check
# -------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed."
    exit 1
}

$pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $pyv -split "\."
$major = [int]$parts[0]
$minor = [int]$parts[1]

if ($major -ne 3 -or $minor -ne 11) {
    Write-Host "Python 3.11 is required. Current: $pyv"
    exit 1
}

Write-Host "Python $pyv OK"

# -------------------------------
# 2. Install Poetry if missing
# -------------------------------
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "Poetry not found - installing..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

    $poetryPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts"
    if (-not ($env:PATH -like "*$poetryPath*")) {
        $env:PATH = $env:PATH + ";" + $poetryPath
    }
} else {
    Write-Host "Poetry found"
}

# -------------------------------
# 3. Configure Poetry
# -------------------------------
Write-Host "Configuring Poetry..."
poetry config virtualenvs.in-project true

# -------------------------------
# 4. Install dependencies
# -------------------------------
Write-Host "Installing dependencies..."
poetry install

Write-Host ""
Write-Host "Setup complete!"
Write-Host "Start the game using: poetry run game"
