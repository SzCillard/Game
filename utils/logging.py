import os

LOGPATH = "log/log.txt"


def delete_log_file():
    if os.path.exists(LOGPATH):
        os.remove(LOGPATH)


def create_log_file():
    delete_log_file()

    with open(LOGPATH, "w") as f:
        f.write("Log start\n")


def logger(message: str) -> None:
    with open(LOGPATH, "a") as f:
        f.write(f"\n {message}")
