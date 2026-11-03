from .auditor import Auditor
from .cli import run


def main():
    return run(Auditor, ["audit"], ".")


if __name__ == "__main__":
    raise SystemExit(main())
