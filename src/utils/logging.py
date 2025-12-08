import logging
import os
from logging.handlers import RotatingFileHandler

from variables.variables import evolution_run

LOG_DIR = "log"
LOG_FILE = "log.txt"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

MAX_SIZE_MB = 10
BACKUP_COUNT = 20

os.makedirs(LOG_DIR, exist_ok=True)


logger = logging.getLogger("commanders_arena")
logger.setLevel(logging.DEBUG)


if not logger.handlers:
    if evolution_run:
        # 🚫 Disable ALL logging during NEAT evolution
        logger.addHandler(logging.NullHandler())
    else:
        # FILE OUTPUT (game mode only)
        file_handler = RotatingFileHandler(
            LOG_PATH,
            maxBytes=MAX_SIZE_MB * 1024 * 1024,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    logger.propagate = False


# ----------------------------------------------------
# Compatibility helpers
# ----------------------------------------------------
def delete_log_file():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)


def create_log_file():
    delete_log_file()
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_PATH, "w") as f:
        f.write("Log start\n")


def log(message: str):
    """Old API compatibility: silently logs only to file."""
    if evolution_run:
        return
    logger.info(message)
