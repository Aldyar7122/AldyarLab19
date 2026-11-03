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
from application.platform import Platform as Tool

data = root / ".data" / ("demo-" + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / "evidence"
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


app = Tool(data / "platform.db")
app.project("P1", "SCM demonstration")
app.project("P2", "Second independent project")
app.item("P1", "CI-001", "main.py", "1.0", "print(1)")
app.baseline("BL-001", "P1", "Reviewer")
app.request("CR-001", "P1", "CI-001", "1.1", "print(2)", "Improve output")
try:
    app.apply("CR-001", hash, "test_full_scenario")
except ValueError as exc:
    blocked = str(exc)
app.decide("CR-001", True, "Reviewer", "Tests and impact reviewed")
app.apply("CR-001", hash, "test_full_scenario")
app.baseline("BL-002", "P1", "Reviewer", previous="BL-001")
release = app.release("P1", "1.0.0", "BL-002")
result = {
    "blocked_before_approval": blocked,
    "comparison": app.compare("BL-001", "BL-002"),
    "release": release,
    "registry": app.report(evidence / "platform-report.json"),
}
app.close()

put_json(evidence / "demo.json", result)
print(json.dumps(result, ensure_ascii=False, indent=2))
