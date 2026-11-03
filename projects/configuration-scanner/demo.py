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
from application.scanner import Scanner as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
target = data / 'scanned'
target.mkdir()
(target / 'app.txt').write_text('version one', encoding='utf-8')
(target / 'obsolete.txt').write_text('old', encoding='utf-8')
app = Tool(target)
first = app.baseline('BL-001', 'Reviewer', hash)
(target / 'app.txt').write_text('version two', encoding='utf-8')
(target / 'obsolete.txt').unlink()
(target / 'new.txt').write_text('added', encoding='utf-8')
second = app.baseline('BL-002', 'Reviewer', hash, previous='BL-001')
result = app.compare('BL-001', 'BL-002', evidence / 'differences.json')
for id in ['BL-001', 'BL-002']:
    shutil.copy2(target / '.scm' / (id + '.json'), evidence / (id + '.json'))

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
