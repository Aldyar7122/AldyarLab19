from .changes import Tracker
from .cli import run


def main():
    return run(Tracker, ["add", "list", "transition", "history", "report"], ".data/store.db")


if __name__ == "__main__":
    raise SystemExit(main())
