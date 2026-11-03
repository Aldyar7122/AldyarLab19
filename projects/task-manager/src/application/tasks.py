"""SQLite task manager with filters and completion statistics."""

from .common import Database, now, text


class Tasks(Database):
    def __init__(self, path):
        super().__init__(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY, title TEXT, assignee TEXT, priority TEXT,
            status TEXT, date TEXT)""")
        self.db.commit()

    @staticmethod
    def _validate(priority, status):
        if priority not in {"low", "normal", "high"}:
            raise ValueError("priority must be low, normal or high")
        if status not in {"planned", "in_progress", "done"}:
            raise ValueError("unknown task status")

    def add(self, title, assignee, priority="normal", status="planned"):
        self._validate(priority, status)
        with self.db:
            row = self.db.execute(
                "INSERT INTO tasks(title,assignee,priority,status,date) VALUES(?,?,?,?,?)",
                (text(title), text(assignee), priority, status, now()),
            )
        return self.get(row.lastrowid)

    def get(self, id):
        rows = self.rows("SELECT * FROM tasks WHERE id=?", (id,))
        if not rows:
            raise ValueError("task does not exist")
        return rows[0]

    def update(self, id, title=None, assignee=None, priority=None, status=None):
        row = self.get(id)
        for key, value in {"title": title, "assignee": assignee, "priority": priority, "status": status}.items():
            if value is not None:
                row[key] = text(value)
        self._validate(row["priority"], row["status"])
        with self.db:
            self.db.execute(
                "UPDATE tasks SET title=?,assignee=?,priority=?,status=? WHERE id=?",
                (row["title"], row["assignee"], row["priority"], row["status"], id),
            )
        return self.get(id)

    def delete(self, id):
        row = self.get(id)
        with self.db:
            self.db.execute("DELETE FROM tasks WHERE id=?", (id,))
        return row

    def list(self, assignee=None, priority=None, status=None):
        filters = {k: v for k, v in locals().items() if k != "self" and v is not None}
        sql = "SELECT * FROM tasks"
        if filters:
            sql += " WHERE " + " AND ".join(f"{key}=?" for key in filters)
        return self.rows(sql + " ORDER BY id", tuple(filters.values()))

    def statistics(self):
        rows = self.list()
        done = sum(row["status"] == "done" for row in rows)
        return {"total": len(rows), "done": done, "completion_percent": round(done / len(rows) * 100, 2) if rows else 0}
