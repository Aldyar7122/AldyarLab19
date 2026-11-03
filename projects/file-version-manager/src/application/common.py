"""Small standard-library helpers shared by the standalone applications."""

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def now():
    return datetime.now(UTC).isoformat()


def text(value, field="value"):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value.strip()


def positive(value):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("quantity must be a positive integer")
    return value


def commit_hash(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError("a full Git commit hash is required")
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


class Database:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")

    def rows(self, sql, args=()):
        return [dict(row) for row in self.db.execute(sql, args)]

    def close(self):
        self.db.close()
