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
from application.warehouse import Warehouse as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
app = Tool(data / 'warehouse.db')
app.add('NB-001', 'Notebook', 'Stationery')
app.move('NB-001', 'receipt', 20)
app.move('NB-001', 'writeoff', 7)
try:
    app.move('NB-001', 'writeoff', 100)
except ValueError as exc:
    rejected = str(exc)
result = {'stock': app.report(), 'journal': app.journal(), 'rejected_writeoff': rejected}
app.close()

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
