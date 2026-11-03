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
from application.versions import Manager as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
app = Tool(data / 'documents')
app.create('lesson.txt', 'Git basics\nOld sentence\n')
first = app.save('lesson.txt')
app.edit('lesson.txt', 'Git basics\nNew sentence\nCI added\n')
second = app.save('lesson.txt')
result = {'first': first, 'second': second,
          'comparison': app.compare('lesson.txt', first['id'], second['id']),
          'restored': app.restore('lesson.txt', first['id']),
          'history_length': len(app.versions('lesson.txt'))}

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
