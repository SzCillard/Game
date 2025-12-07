# utils/logging.py

import logging
import os
from logging.handlers import RotatingFileHandler

from variables.variables import evolution_run

# ===================================================================
# CONFIG
# ===================================================================

LOG_DIR = "log"
LOG_FILE = "log.txt"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

MAX_SIZE_MB = 10
BACKUP_COUNT = 20

os.makedirs(LOG_DIR, exist_ok=True)


# ===================================================================
# LOGGER SETUP
# ===================================================================

logger = logging.getLogger("commanders_arena")
logger.setLevel(logging.DEBUG)  # Master logging level (file gets everything)

# Prevent duplicate handlers (important when reloading modules)
if not logger.handlers:
    # File handler (writes DEBUG+)
    file_handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=MAX_SIZE_MB * 1024 * 1024,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler (writes INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Avoid propagation to root logger
    logger.propagate = False


# ===================================================================
# Compatibility Functions
# (keep your old API so nothing else breaks)
# ===================================================================


def delete_log_file():
    """Delete the main log file."""
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)


def create_log_file():
    """Reset the log file before game starts."""
    delete_log_file()
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        f.write("Log start\n")


def log(message: str) -> None:
    """
    Backwards-compatible logger for parts of the code that used:
        logger.info("message")

    If evolution_run == True → suppress logs during NEAT training.
    """
    if evolution_run:
        return  # suppress all logging during training

    logger.info(message)
