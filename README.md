______________________________________________________________________

# 📘 Commanders' Arena

*A turn-based tactical strategy game powered by a NEAT-based AI.*

______________________________________________________________________

# 🚀 Quick Start

This project uses **Poetry** for dependency management and provides fully automated setup scripts for:

- **Linux / macOS** → `setup.sh`
- **Windows (PowerShell)** → `setup.ps1`

After cloning the repository, the game can be installed and played within minutes.

______________________________________________________________________

# 📥 1. Clone the Repository or Download the ZIP

```bash
git clone https://github.com/SzCillard/Game.git
```

Change directory...

```bash
cd Game
```

______________________________________________________________________

# 🛠️ 2. Automatic Setup

## ▶️ Linux / macOS

```bash
chmod +x setup.sh && \
./setup.sh
```

This script will:

- Verify Python 3.11
- Install Poetry (if missing)
- Configure Poetry to create a local `.venv` in the project directory
- Install all dependencies

______________________________________________________________________

## ▶️ Windows (PowerShell)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser; `
./setup.ps1
```

This performs the same steps as the Linux/macOS setup script.

______________________________________________________________________

# 🎮 3. Running the Game

Please take the survey about the game once 
you tested the two agent: https://forms.gle/Z14zq54Q93AYP85C6

After installation:

```bash
poetry run game
```

This launches the Commanders’ Arena with an agent called **"NEATAgent"**.

❗️**IMPORTANT**❗️

Try out **"MCTSAgent"** agent as well please!!!
 
Run this:

```bash
poetry run game --agent MCTSAgent
```
______________________________________________________________________

# 🕹 Gameplay Guide

This section explains **how to use the UI**, **how to control units**, and **how turns work**, based directly on your UI + Renderer behavior.

______________________________________________________________________

## 📜 Main Menu

When the game starts, you will see:

- **Start Game**
- **Quit**

You may use:

- **Mouse** → Click buttons
- **Arrow Keys / W / S** → Navigate
- **Enter / Space** → Confirm selection

______________________________________________________________________

## 🛡 Draft Phase – Build Your Army

You begin with **100 funds**.
The draft screen shows:

- Unit types: Swordsman, Archer, Horseman, Spearman
- Their **cost, HP, Armor, Attack, Range, Movement**
- Your **remaining funds**
- Buttons to **add (+)** or **remove (–)** units

When satisfied with your army, click **Start Battle**.

______________________________________________________________________

# ⚔️ In-Game Controls (During Battle)

The battlefield contains:

- A **15×15 grid**

- A **sidebar** on the left with:

  - Current turn indicator
  - Selected unit stats
  - Terrain bonuses
  - Buttons: **End Turn**, **Menu**, **Quit**, **Help**

______________________________________________________________________

## 🎯 Selecting Units

**Left-click** any of your units to select it.
A unit can only be selected if:

- It belongs to the player (Team 1)
- It has not yet finished its action for the turn

Selected units are highlighted with a **yellow border**.

______________________________________________________________________

## 🚶 Moving Units

When a unit is selected:

1. **Blue squares** indicate movement range
1. Click any highlighted tile to move there
1. Movement consumes **movement points**
1. Units can move until their **movement points** > 0, then you can't even select them
1. A unit cannot move after attacking

If you click a non-reachable tile, nothing happens.

______________________________________________________________________

## 🗡 Attacking

If you click an **enemy** while a unit is selected:

- If the enemy is in range (1 tile for melee, up to 3 for archers)
- Your unit will attack
- **Melee enemies retaliate** if they survive

Attacks end the unit’s action for the turn.

**Red tiles** indicate enemies in attack range.

______________________________________________________________________

## 🧱 Terrain Bonuses

The sidebar shows terrain bonuses for the currently selected unit:

- **Hills** → +20% Defense, +10% Attack
- **Water** → Slight Defense bonus, Attack penalty
- **Plains** → No bonuses

______________________________________________________________________

## ⏳ Ending Your Turn

You may end your turn manually:

- Press **End Turn** in the sidebar
- Or automatically when all your units have finished acting

The AI then takes its turn.

______________________________________________________________________

## 🩸 Damage Numbers & Health Bars

- Floating red numbers show recent damage
- Units display green/yellow/red HP bars depending on remaining health

______________________________________________________________________

## 🏆 Winning

The battle ends when:

- One side loses all units
- Or both sides are eliminated → **Draw**

A victory/defeat screen appears briefly before returning to menu.

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

If you prefer not to use the setup scripts:

### Linux / macOS

```bash
pip install poetry && \
poetry config virtualenvs.in-project true && \
poetry install && \
poetry run game
```

### Windows (PowerShell)

```powershell
pip install poetry; `
poetry config virtualenvs.in-project true; `
poetry install; `
poetry run game
```

______________________________________________________________________

# 🎉 You're Ready to Play!

If everything installed correctly, the game window will open and you can begin commanding your army.

Enjoy **Commanders' Arena**! 🛡️⚔️
May your tactics be sharp and your units loyal.

______________________________________________________________________
