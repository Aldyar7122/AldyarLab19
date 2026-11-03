from .cli import run
from .scanner import Scanner


def main():
    return run(Scanner, ["scan", "baseline", "load", "compare"], ".")


if __name__ == "__main__":
    raise SystemExit(main())
