______________________________________________________________________

# 📘 Commanders' Arena

*A turn-based tactical strategy game powered by a NEAT-based AI.*

______________________________________________________________________

# 🚀 Quick Start

This project uses **Poetry** for dependency management and provides fully automated setup scripts for:

- **Linux / macOS** → `setup.sh`
- **Windows (PowerShell)** → `setup.ps1`

After cloning the repository, you can start playing within minutes.

______________________________________________________________________

# 📥 1. Clone the Repository

```bash
git clone https://github.com/SzCillard/Game.git && \
cd Game
```

______________________________________________________________________

# 🛠️ 2. Automatic Setup

## ▶️ Linux / macOS

Run the included installation script:

```bash
chmod +x setup.sh && \
./setup.sh
```

This script will:

- Verify Python 3.11
- Install Poetry (if missing)
- Configure Poetry to use a project-local `.venv`
- Install all dependencies

______________________________________________________________________

## ▶️ Windows (PowerShell)

Run the setup script:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; `
./setup.ps1
```

This performs the same steps as the Linux setup script.

______________________________________________________________________

# 🎮 3. Running the Game

Once installation completes, launch the game with:

```bash
poetry run game
```

Or on Windows PowerShell:

```powershell
poetry run game
```

______________________________________________________________________

# 📂 Project Structure (Short Overview)

```
src/
  ai/         – NEAT AI agent implementation
  backend/    – Game logic & state management
  frontend/   – Renderer & UI
  api/        – Game API layer
assets/       – Images, icons, music, NEAT genomes
setup.sh      – Linux/macOS auto-installer
setup.ps1     – Windows auto-installer
```

______________________________________________________________________

# 🔧 Optional: Manual Installation (Advanced Users)

If you prefer not to use the setup script:

**Linux / macOS:**

```bash
pip install poetry && \
poetry config virtualenvs.in-project true && \
poetry install && \
poetry run game
```

**Windows (PowerShell):**

```powershell
pip install poetry; `
poetry config virtualenvs.in-project true; `
poetry install; `
poetry run game
```

______________________________________________________________________

# 🎉 You're Ready to Play!

If everything installed correctly, the game window will open and you can start a new battle.

Enjoy Commanders' Arena! 🛡️⚔️

______________________________________________________________________
