"""Recursive SHA-256 inventory and append-only approved baselines."""

import fnmatch
import hashlib
import json
from pathlib import Path

from .common import commit_hash, now, text, write_json


class Scanner:
    def __init__(self, path):
        self.root = Path(path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.state = self.root / ".scm"
        self.state.mkdir(exist_ok=True)

    def scan(self, exclude=None):
        excluded = {".git", "__pycache__", "venv", ".venv", ".scm", ".pytest_cache", ".ruff_cache"}
        result = []
        for path in sorted(self.root.rglob("*")):
            rel = path.relative_to(self.root)
            if path.is_symlink() or any(part in excluded for part in rel.parts):
                continue
            if any(fnmatch.fnmatch(rel.as_posix(), rule) or rule in rel.parts for rule in (exclude or [])):
                continue
            if path.is_file():
                data = path.read_bytes()
                result.append(
                    {
                        "id": "CI-" + hashlib.sha256(rel.as_posix().encode()).hexdigest()[:12],
                        "path": rel.as_posix(),
                        "size": len(data),
                        "version": hashlib.sha256(data).hexdigest()[:12],
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
        return result

    def _path(self, id):
        if not text(id).replace("-", "").replace("_", "").isalnum():
            raise ValueError("invalid baseline ID")
        return self.state / (id + ".json")

    def load(self, id):
        path = self._path(id)
        if not path.exists():
            raise ValueError("baseline does not exist")
        return json.loads(path.read_text(encoding="utf-8"))

    def baseline(self, id, approver, commit, previous=None, exclude=None):
        path = self._path(id)
        if previous:
            self.load(previous)
        data = {
            "id": id,
            "date": now(),
            "approver": text(approver),
            "commit_hash": commit_hash(commit),
            "previous": previous,
            "exclude": exclude or [],
            "items": self.scan(exclude),
        }
        try:
            with path.open("x", encoding="utf-8") as out:
                json.dump(data, out, ensure_ascii=False, indent=2)
        except FileExistsError as exc:
            raise ValueError("approved baseline is immutable; use a new ID") from exc
        return data

    @staticmethod
    def _diff(old, new):
        a = {v["path"]: v["sha256"] for v in old}
        b = {v["path"]: v["sha256"] for v in new}
        return {
            "added": sorted(b.keys() - a.keys()),
            "removed": sorted(a.keys() - b.keys()),
            "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
        }

    def compare(self, old, new=None, output=None):
        base = self.load(old)
        current = self.load(new)["items"] if new else self.scan(base["exclude"])
        result = {
            "baseline": old,
            "compared_to": new or "working_tree",
            "time": now(),
            **self._diff(base["items"], current),
        }
        with (self.state / "history.jsonl").open("a", encoding="utf-8") as history:
            history.write(json.dumps(result, ensure_ascii=False) + "\n")
        if output:
            write_json(output, result)
        return result
