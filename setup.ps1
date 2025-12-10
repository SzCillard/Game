Write-Host "Commanders' Arena - Automatic Setup"
Write-Host "---------------------------------------"

# Python version check
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed."
    exit 1
}

$pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$major, $minor = $pyv -split "\."

if ($major -lt 3 -or $minor -lt 11) {
    Write-Host "Python 3.11+ required. Current: $pyv"
    exit 1
}

Write-Host "Python $pyv OK"

# Install Poetry if missing
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "Poetry not found — installing..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    $poetryPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts"
    if (-not ($env:PATH -like "*$poetryPath*")) {
        $env:PATH += ";$poetryPath"
    }
} else {
    Write-Host "Poetry found"
}

# Configure Poetry
Write-Host "Configuring Poetry..."
poetry config virtualenvs.in-project true

# Install dependencies
Write-Host "Installing dependencies..."
poetry install

Write-Host "`nSetup complete!"
Write-Host "Start the game using: poetry run game"
