from .cli import run
from .tasks import Tasks


def main():
    return run(Tasks, ["add", "get", "update", "delete", "list", "statistics"], ".data/store.db")


if __name__ == "__main__":
    raise SystemExit(main())
