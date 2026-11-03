from .cli import run
from .traceability import Traceability


def main():
    return run(
        Traceability,
        [
            "project",
            "item",
            "items",
            "request",
            "requests",
            "decide",
            "apply",
            "baseline",
            "get_baseline",
            "compare",
            "release",
            "report",
            "verify",
            "chains",
            "matrix",
            "audit",
        ],
        ".data/store.db",
    )


if __name__ == "__main__":
    raise SystemExit(main())
