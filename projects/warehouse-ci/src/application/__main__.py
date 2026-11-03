from .cli import run
from .warehouse import Warehouse


def main():
    return run(Warehouse, ["add", "get", "update", "delete", "move", "search", "report", "journal"], ".data/store.db")


if __name__ == "__main__":
    raise SystemExit(main())
