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
from application.tasks import Tasks as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
app = Tool(data / 'tasks.db')
a = app.add('Implement filters', 'Student', 'high')
app.add('Write report', 'Student', 'normal', 'done')
app.update(a['id'], status='done')
result = {'filtered': app.list(assignee='Student', priority='high', status='done'),
          'statistics': app.statistics(), 'conflict': json.loads((evidence / 'conflict.json').read_text())}
app.close()

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
