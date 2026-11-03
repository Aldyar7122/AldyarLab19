"""Immutable text revisions with non-destructive restoration."""

import difflib
import json
import uuid
from pathlib import Path

from .common import now, text, write_json


class Manager:
    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def _file(self, name):
        name = text(name, "document")
        if Path(name).name != name or name in {".", ".."} or "/" in name or "\\" in name:
            raise ValueError("document must be a simple filename")
        return self.path / (name + ".json")

    def _read(self, name):
        path = self._file(name)
        if not path.exists():
            raise ValueError("document does not exist")
        return json.loads(path.read_text(encoding="utf-8"))

    def create(self, name, content=""):
        path = self._file(name)
        if path.exists():
            raise ValueError("document already exists")
        if not isinstance(content, str):
            raise ValueError("content must be text")
        write_json(path, {"content": content, "versions": []})
        return {"document": name, "content": content}

    def edit(self, name, content):
        data = self._read(name)
        if not isinstance(content, str):
            raise ValueError("content must be text")
        data["content"] = content
        write_json(self._file(name), data)
        return {"content": content}

    def save(self, name):
        data = self._read(name)
        revision = {"id": uuid.uuid4().hex, "time": now(), "content": data["content"]}
        data["versions"].append(revision)
        write_json(self._file(name), data)
        return revision

    def versions(self, name):
        return self._read(name)["versions"]

    def _version(self, name, version):
        for item in self.versions(name):
            if item["id"] == version:
                return item
        raise ValueError("version does not exist")

    def compare(self, name, old, new):
        a = self._version(name, old)["content"].splitlines()
        b = self._version(name, new)["content"].splitlines()
        return {"diff": "\n".join(difflib.unified_diff(a, b, old, new, lineterm=""))}

    def restore(self, name, version):
        self.edit(name, self._version(name, version)["content"])
        revision = self.save(name)
        revision["restored_from"] = version
        return revision
