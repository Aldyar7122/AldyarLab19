"""Reproducible demonstration using isolated local data."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'src'))
from application.changes import Tracker as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
app = Tool(data / 'changes.db')
hashes = subprocess.check_output(['git', 'log', '-2', '--format=%H'], cwd=root, text=True).splitlines()
for number, digest in enumerate(hashes, 1):
    id = f'CR-{number:03d}'
    app.add(id, 'Student', 'feature', f'Configuration update {number}')
    app.transition(id, 'in_progress')
    app.transition(id, 'completed', digest)
result = app.report(evidence / 'change-report.json')
app.close()

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
