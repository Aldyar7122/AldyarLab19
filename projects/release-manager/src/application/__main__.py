from .cli import run
from .releases import Releases


def main():
    return run(Releases, ["current", "register", "bump", "check_tag"], ".")


if __name__ == "__main__":
    raise SystemExit(main())
