"""Reproducible demonstration using isolated local data."""

import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "src"))
from application.traceability import Traceability as Tool

data = root / ".data" / ("demo-" + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


app = Tool(data / "traceability.db")
app.project("P1", "Evidence project")
app.item("P1", "CI-001", "main.py", "1.0", "print(1)")
app.request("CR-001", "P1", "CI-001", "1.1", "print(2)", "Reviewed change")
app.decide("CR-001", True, "Reviewer", "Approved after impact analysis")
app.apply("CR-001", hash, "test_chain")
(data / "main.py").write_text("print(2)", encoding="utf-8")
app.baseline("BL-001", "P1", "Reviewer")
before = app.verify("BL-001", data)
(data / "main.py").write_text("external change", encoding="utf-8")
after = app.verify("BL-001", data)
app.release("P1", "1.0.0", "BL-001")
result = {"chain_audit": app.audit(evidence / "traceability.json"), "before": before, "after": after}
put_json(evidence / "matrix.json", app.matrix())
columns = ["process", "scmp", "function", "test", "evidence", "status", "limitation"]
with (evidence / "matrix.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    writer.writerows(app.matrix())
app.close()

put_json(evidence / "demo.json", result)
print(json.dumps(result, ensure_ascii=False, indent=2))
