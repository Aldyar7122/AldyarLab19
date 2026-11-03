from .cli import run
from .versions import Manager


def main():
    return run(Manager, ["create", "edit", "save", "versions", "compare", "restore"], ".data/documents")


if __name__ == "__main__":
    raise SystemExit(main())
