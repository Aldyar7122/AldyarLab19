"""Transactional stock accounting; stock and journal update together."""

import sqlite3

from .common import Database, now, text


class Warehouse(Database):
    def __init__(self, path):
        super().__init__(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS products(
          sku TEXT PRIMARY KEY, name TEXT, category TEXT, stock INTEGER NOT NULL CHECK(stock>=0),
          active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS operations(
          id INTEGER PRIMARY KEY, sku TEXT REFERENCES products(sku), kind TEXT,
          quantity INTEGER CHECK(quantity>0), date TEXT);
        """)

    def add(self, sku, name, category):
        try:
            with self.db:
                self.db.execute(
                    "INSERT INTO products(sku,name,category,stock) VALUES(?,?,?,0)",
                    (text(sku), text(name), text(category)),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate SKU") from exc
        return self.get(sku)

    def get(self, sku):
        rows = self.rows("SELECT * FROM products WHERE sku=? AND active=1", (sku,))
        if not rows:
            raise ValueError("product does not exist")
        return rows[0]

    def update(self, sku, name, category):
        self.get(sku)
        with self.db:
            self.db.execute("UPDATE products SET name=?,category=? WHERE sku=?", (text(name), text(category), sku))
        return self.get(sku)

    def delete(self, sku):
        row = self.get(sku)
        if row["stock"]:
            raise ValueError("write off stock before deleting product")
        with self.db:
            self.db.execute("UPDATE products SET active=0 WHERE sku=?", (sku,))
        return row

    def move(self, sku, kind, quantity):
        if kind not in {"receipt", "writeoff"}:
            raise ValueError("operation must be receipt or writeoff")
        self.get(sku)
        delta = quantity if kind == "receipt" else -quantity
        with self.db:
            updated = self.db.execute(
                "UPDATE products SET stock=stock+? WHERE sku=? AND active=1 AND stock+?>=0", (delta, sku, delta)
            )
            if updated.rowcount != 1:
                raise ValueError("insufficient stock")
            self.db.execute(
                "INSERT INTO operations(sku,kind,quantity,date) VALUES(?,?,?,?)", (sku, kind, quantity, now())
            )
        return self.get(sku)

    def search(self, query="", category=None):
        return self.rows(
            "SELECT * FROM products WHERE active=1 AND (instr(lower(name),lower(?))>0 "
            "OR instr(lower(sku),lower(?))>0) AND (? IS NULL OR category=?) ORDER BY sku",
            (query, query, category, category),
        )

    def report(self):
        items = self.search()
        return {"items": items, "total_units": sum(row["stock"] for row in items)}

    def journal(self):
        return self.rows("SELECT * FROM operations ORDER BY id")
