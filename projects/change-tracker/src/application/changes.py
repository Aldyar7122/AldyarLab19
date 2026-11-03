"""Persistent change requests with a strictly ordered lifecycle."""

import json

from .common import Database, commit_hash, now, text, write_json


class Tracker(Database):
    def __init__(self, path):
        super().__init__(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS changes(
          id TEXT PRIMARY KEY, author TEXT, date TEXT, kind TEXT,
          description TEXT, status TEXT, commit_hash TEXT);
        CREATE TABLE IF NOT EXISTS history(
          seq INTEGER PRIMARY KEY, change_id TEXT, date TEXT, status TEXT);
        """)

    def add(self, id, author, kind, description):
        values = tuple(text(v) for v in (id, author, kind, description))
        if self.rows("SELECT id FROM changes WHERE id=?", (id,)):
            raise ValueError("duplicate change ID")
        with self.db:
            self.db.execute(
                "INSERT INTO changes VALUES(?,?,?,?,?,'planned',NULL)",
                (values[0], values[1], now(), values[2], values[3]),
            )
            self.db.execute("INSERT INTO history(change_id,date,status) VALUES(?,?,'planned')", (id, now()))
        return self.list(id=id)[0]

    def list(self, author=None, kind=None, status=None, id=None):
        filters = {k: v for k, v in locals().items() if k != "self" and v is not None}
        sql = "SELECT * FROM changes"
        if filters:
            sql += " WHERE " + " AND ".join(f"{key}=?" for key in filters)
        return self.rows(sql + " ORDER BY date,id", tuple(filters.values()))

    def transition(self, id, status, hash=None):
        rows = self.list(id=id)
        if not rows:
            raise ValueError("unknown change ID")
        allowed = {"planned": "in_progress", "in_progress": "completed"}
        if allowed.get(rows[0]["status"]) != status:
            raise ValueError("invalid status transition")
        if status == "completed":
            hash = commit_hash(hash)
        with self.db:
            self.db.execute("UPDATE changes SET status=?,commit_hash=? WHERE id=?", (status, hash, id))
            self.db.execute("INSERT INTO history(change_id,date,status) VALUES(?,?,?)", (id, now(), status))
        return self.list(id=id)[0]

    def history(self, id):
        return self.rows("SELECT * FROM history WHERE change_id=? ORDER BY seq", (id,))

    def report(self, output=None):
        result = {"generated": now(), "changes": self.list(), "history": self.rows("SELECT * FROM history")}
        if output:
            write_json(output, result)
        return json.loads(json.dumps(result))
