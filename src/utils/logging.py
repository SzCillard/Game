import os

from variables.variables import evolution_run

ENABLE_LOGGING = False
LOGPATH = "log/log.txt"


def delete_log_file():
    if os.path.exists(LOGPATH):
        os.remove(LOGPATH)


def create_log_file():
    delete_log_file()
    os.makedirs(os.path.dirname(LOGPATH), exist_ok=True)
    with open(LOGPATH, "w") as f:
        f.write("Log start\n")


def logger(message: str) -> None:
    if evolution_run is False:
        with open(LOGPATH, "a") as f:
            f.write(f"\n {message}")
