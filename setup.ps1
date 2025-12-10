Write-Host "Commanders' Arena - Automatic Setup"
Write-Host "---------------------------------------"

# -------------------------------
# 1. Check for Python
# -------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Installing Python 3.11 for the current user..."

    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installer = "python311_installer.exe"

    Write-Host "Downloading Python 3.11..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installer

    Write-Host "Running installer (no admin required)..."
    Start-Process -FilePath ".\$installer" -ArgumentList "/quiet InstallLauncherAllUsers=0 PrependPath=1" -Wait

    Remove-Item $installer -Force

    # Refresh PATH for the current terminal session
    $pythonUserPath = "$env:LOCALAPPDATA\Programs\Python\Python311\"
    $scriptsPath = "$pythonUserPath\Scripts\"

    if (-not ($env:PATH -like "*$pythonUserPath*")) {
        $env:PATH = "$env:PATH;$pythonUserPath;$scriptsPath"
    }

    Write-Host "Python 3.11 installed successfully!"
}

# Re-check Python version
$pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $pyv -split "\."
$major = [int]$parts[0]
$minor = [int]$parts[1]

if ($major -ne 3 -or $minor -ne 11) {
    Write-Host "Python 3.11 is required. Current detected: $pyv"
    exit 1
}

Write-Host "Python $pyv OK"

# -------------------------------
# 2. Install Poetry if missing
# -------------------------------
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "Poetry not found — installing..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

    $poetryPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts"
    if (-not ($env:PATH -like "*$poetryPath*")) {
        $env:PATH = $env:PATH + ";" + $poetryPath
    }

    Write-Host "Poetry installed"
}
else {
    Write-Host "Poetry already installed"
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
Write-Host "Start the game using:  poetry run game"
