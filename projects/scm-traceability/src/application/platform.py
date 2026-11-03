"""Multi-project SCM registry. Approval gates changes and baseline release."""

import hashlib
import json
import sqlite3

from .common import Database, commit_hash, now, text, write_json


class Platform(Database):
    def __init__(self, path):
        super().__init__(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS items(
          project TEXT REFERENCES projects(id), id TEXT, path TEXT, version TEXT, sha256 TEXT,
          PRIMARY KEY(project,id));
        CREATE TABLE IF NOT EXISTS item_versions(
          project TEXT, id TEXT, version TEXT, sha256 TEXT, date TEXT,
          PRIMARY KEY(project,id,version), FOREIGN KEY(project,id) REFERENCES items(project,id));
        CREATE TABLE IF NOT EXISTS requests(
          id TEXT PRIMARY KEY, project TEXT REFERENCES projects(id), item TEXT, version TEXT,
          sha256 TEXT, description TEXT, status TEXT, decision TEXT, approver TEXT,
          commit_hash TEXT, test TEXT);
        CREATE TABLE IF NOT EXISTS baselines(
          id TEXT PRIMARY KEY, project TEXT REFERENCES projects(id), previous TEXT REFERENCES baselines(id),
          approver TEXT, date TEXT, items TEXT);
        CREATE TABLE IF NOT EXISTS releases(
          project TEXT REFERENCES projects(id), version TEXT, baseline TEXT REFERENCES baselines(id),
          date TEXT, PRIMARY KEY(project,version));
        CREATE TABLE IF NOT EXISTS history(
          seq INTEGER PRIMARY KEY, project TEXT, event TEXT, ref TEXT, date TEXT, detail TEXT);
        CREATE TRIGGER IF NOT EXISTS immutable_baseline_update BEFORE UPDATE ON baselines
          BEGIN SELECT RAISE(ABORT,'baseline is immutable'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_baseline_delete BEFORE DELETE ON baselines
          BEGIN SELECT RAISE(ABORT,'baseline is immutable'); END;
        """)

    def _event(self, project, event, ref, detail=""):
        self.db.execute(
            "INSERT INTO history(project,event,ref,date,detail) VALUES(?,?,?,?,?)", (project, event, ref, now(), detail)
        )

    def project(self, id, name):
        try:
            with self.db:
                self.db.execute("INSERT INTO projects VALUES(?,?)", (text(id), text(name)))
                self._event(id, "project_registered", id)
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate project") from exc
        return {"id": id, "name": name}

    def _project(self, id):
        if not self.rows("SELECT id FROM projects WHERE id=?", (id,)):
            raise ValueError("project does not exist")

    def item(self, project, id, path, version, content):
        self._project(project)
        if not isinstance(content, str):
            raise ValueError("content must be text")
        digest = hashlib.sha256(content.encode()).hexdigest()
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO items VALUES(?,?,?,?,?)", (project, text(id), text(path), text(version), digest)
                )
                self.db.execute("INSERT INTO item_versions VALUES(?,?,?,?,?)", (project, id, version, digest, now()))
                self._event(project, "item_registered", id)
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate item") from exc
        return self.items(project)

    def items(self, project):
        return self.rows("SELECT * FROM items WHERE project=? ORDER BY id", (project,))

    def request(self, id, project, item, version, content, description):
        if not isinstance(content, str):
            raise ValueError("content must be text")
        current = self.rows("SELECT * FROM items WHERE project=? AND id=?", (project, item))
        if not current:
            raise ValueError("item does not exist in project")
        if self.rows(
            "SELECT version FROM item_versions WHERE project=? AND id=? AND version=?", (project, item, version)
        ):
            raise ValueError("item version is already registered")
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO requests VALUES(?,?,?,?,?,?,'pending',NULL,NULL,NULL,NULL)",
                    (
                        text(id),
                        project,
                        item,
                        text(version),
                        hashlib.sha256(content.encode()).hexdigest(),
                        text(description),
                    ),
                )
                self._event(project, "change_requested", id)
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate request ID") from exc
        return self.requests(id)[0]

    def requests(self, id=None):
        return self.rows("SELECT * FROM requests" + (" WHERE id=?" if id else "") + " ORDER BY id", (id,) if id else ())

    def decide(self, id, approve, approver, reason):
        rows = self.requests(id)
        if not rows or rows[0]["status"] != "pending" or type(approve) is not bool:
            raise ValueError("decision requires a pending request and a boolean")
        with self.db:
            self.db.execute(
                "UPDATE requests SET status=?,decision=?,approver=? WHERE id=?",
                ("approved" if approve else "rejected", text(reason), text(approver), id),
            )
            self._event(rows[0]["project"], "decision", id, "approved" if approve else "rejected")
        return self.requests(id)[0]

    def apply(self, id, commit, test):
        rows = self.requests(id)
        if not rows or rows[0]["status"] != "approved":
            raise ValueError("only an approved request can be applied once")
        row = rows[0]
        commit_hash(commit)
        text(test)
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO item_versions VALUES(?,?,?,?,?)",
                    (row["project"], row["item"], row["version"], row["sha256"], now()),
                )
                self.db.execute(
                    "UPDATE items SET version=?,sha256=? WHERE project=? AND id=?",
                    (row["version"], row["sha256"], row["project"], row["item"]),
                )
                self.db.execute(
                    "UPDATE requests SET status='applied',commit_hash=?,test=? WHERE id=?", (commit, test, id)
                )
                self._event(row["project"], "change_applied", id, commit)
        except sqlite3.IntegrityError as exc:
            raise ValueError("version already applied by another request") from exc
        return self.requests(id)[0]

    def baseline(self, id, project, approver, previous=None):
        self._project(project)
        items = self.items(project)
        if not items:
            raise ValueError("cannot approve an empty baseline")
        if previous:
            base = self.get_baseline(previous)
            if base["project"] != project:
                raise ValueError("previous baseline belongs to another project")
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO baselines VALUES(?,?,?,?,?,?)",
                    (text(id), project, previous, text(approver), now(), json.dumps(items)),
                )
                self._event(project, "baseline_approved", id)
        except sqlite3.IntegrityError as exc:
            raise ValueError("baseline already exists") from exc
        return self.get_baseline(id)

    def get_baseline(self, id):
        rows = self.rows("SELECT * FROM baselines WHERE id=?", (id,))
        if not rows:
            raise ValueError("baseline does not exist")
        row = rows[0]
        row["items"] = json.loads(row["items"])
        return row

    def compare(self, old, new):
        a, b = self.get_baseline(old), self.get_baseline(new)
        if a["project"] != b["project"]:
            raise ValueError("baselines belong to different projects")
        a = {i["id"]: i for i in a["items"]}
        b = {i["id"]: i for i in b["items"]}
        return {
            "added": sorted(b.keys() - a.keys()),
            "removed": sorted(a.keys() - b.keys()),
            "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
        }

    def release(self, project, version, baseline):
        import re

        if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
            raise ValueError("invalid release version")
        if self.get_baseline(baseline)["project"] != project:
            raise ValueError("baseline belongs to another project")
        try:
            with self.db:
                self.db.execute("INSERT INTO releases VALUES(?,?,?,?)", (project, version, baseline, now()))
                self._event(project, "release_registered", version, baseline)
        except sqlite3.IntegrityError as exc:
            raise ValueError("release already registered") from exc
        return {"project": project, "version": version, "baseline": baseline}

    def report(self, output=None):
        result = {
            table: self.rows(f"SELECT * FROM {table}")
            for table in ("projects", "items", "item_versions", "requests", "baselines", "releases", "history")
        }
        if output:
            write_json(output, result)
        return result
