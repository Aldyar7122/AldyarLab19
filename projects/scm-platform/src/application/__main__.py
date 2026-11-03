from .cli import run
from .platform import Platform


def main():
    return run(
        Platform,
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
            "request_history",
            "baseline_history",
            "list_releases",
        ],
        ".data/store.db",
    )


if __name__ == "__main__":
    raise SystemExit(main())
