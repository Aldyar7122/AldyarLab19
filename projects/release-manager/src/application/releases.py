"""Strict numeric SemVer releases and tag validation."""

import json
import re
import tomllib
from pathlib import Path

from .common import now, text, write_json


def parse(version):
    if not isinstance(version, str) or not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError("version must be MAJOR.MINOR.PATCH without leading zeros")
    return tuple(map(int, version.split(".")))


class Releases:
    def __init__(self, path):
        self.root = Path(path)

    def current(self):
        try:
            data = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))
            version = data["project"]["version"]
            parse(version)
            return version
        except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
            raise ValueError("missing or invalid pyproject.toml version") from exc

    def _history(self):
        path = self.root / "releases.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

    def register(self, version, changes):
        old = self.current()
        if parse(version) < parse(old):
            raise ValueError("version cannot decrease")
        history = self._history()
        if version in [row["version"] for row in history]:
            raise ValueError("version is already registered")
        changes = text(changes, "changes")
        source = (self.root / "pyproject.toml").read_text(encoding="utf-8")
        # Change only the project table, never an unrelated tool version.
        section = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[|\Z)", source)
        if section is None:
            raise ValueError("missing project table")
        content, count = re.subn(
            r"(?m)^version\s*=\s*[\"\x27][^\"\x27]+[\"\x27]", f'version = "{version}"', section.group(1), count=1
        )
        if count != 1:
            raise ValueError("project version must be on its own line")
        source = source[: section.start(1)] + content + source[section.end(1) :]
        (self.root / "pyproject.toml").write_text(source, encoding="utf-8")
        entry = {"version": version, "date": now()[:10], "changes": changes}
        history.append(entry)
        write_json(self.root / "releases.json", history)
        changelog = self.root / "CHANGELOG.md"
        previous = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n"
        changelog.write_text(previous + f"\n## {version} {entry['date']}\n\n- {changes}\n", encoding="utf-8")
        return entry

    def bump(self, part, changes):
        values = list(parse(self.current()))
        if part.upper() not in {"MAJOR", "MINOR", "PATCH"}:
            raise ValueError("part must be MAJOR, MINOR or PATCH")
        index = {"MAJOR": 0, "MINOR": 1, "PATCH": 2}[part.upper()]
        values[index] += 1
        for pos in range(index + 1, 3):
            values[pos] = 0
        return self.register(".".join(map(str, values)), changes)

    def check_tag(self, tag):
        if not tag or not isinstance(tag, str) or not tag.startswith("v"):
            raise ValueError("release requires a vMAJOR.MINOR.PATCH Git tag")
        parse(tag[1:])
        if tag[1:] != self.current():
            raise ValueError(f"tag {tag} differs from package version {self.current()}")
        return {"tag": tag, "version": self.current(), "valid": True}
