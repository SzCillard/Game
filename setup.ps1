Write-Host "Commanders' Arena - Automatic Setup"
Write-Host "---------------------------------------"

# -------------------------------
# 1. Check for Python
# -------------------------------
$needPython = $false

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Python 3.11 will be installed."
    $needPython = $true
} else {
    $pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $parts = $pyv -split "\."
    $major = [int]$parts[0]
    $minor = [int]$parts[1]

    if ($major -ne 3 -or $minor -ne 11) {
        Write-Host "Detected Python $pyv but Python 3.11 is required. Installing Python 3.11..."
        $needPython = $true
    } else {
        Write-Host "Python $pyv OK"
    }
}

# -------------------------------
# Install Python 3.11 (user mode)
# -------------------------------
if ($needPython) {
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installer = "python311_installer.exe"

    Write-Host "Downloading Python 3.11..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installer

    Write-Host "Running installer..."
    Start-Process -FilePath ".\$installer" -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait

    Remove-Item $installer -Force

    # Update PATH in this session
    $pythonUserPath = "$env:LOCALAPPDATA\Programs\Python\Python311"
    $scriptsPath = "$pythonUserPath\Scripts"

    if (-not ($env:PATH -like "*$pythonUserPath*")) {
        $env:PATH = "$env:PATH;$pythonUserPath;$scriptsPath"
    }

    Write-Host "Python 3.11 installed."
}

# -------------------------------
# Re-check Python version
# -------------------------------
$pyv = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$parts = $pyv -split "\."
$major = [int]$parts[0]
$minor = [int]$parts[1]

if ($major -ne 3 -or $minor -ne 11) {
    Write-Host "ERROR: Python 3.11 could not be detected after installation."
    exit 1
}

Write-Host "Python $pyv OK"

# -------------------------------
# 2. Install Poetry
# -------------------------------
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Poetry..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

    $poetryPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts"
    if (-not ($env:PATH -like "*$poetryPath*")) {
        $env:PATH = "$env:PATH;$poetryPath"
    }

    Write-Host "Poetry installed."
} else {
    Write-Host "Poetry already installed."
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
Write-Host "Run the game using: poetry run game"
