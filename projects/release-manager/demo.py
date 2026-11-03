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
from application.releases import Releases as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
shutil.copy2(root / 'pyproject.toml', data / 'pyproject.toml')
app = Tool(data)
app.register('1.0.0', 'Initial reviewed baseline')
patch = app.bump('PATCH', 'Correct input handling')
minor = app.bump('MINOR', 'Add reporting')
major = app.bump('MAJOR', 'Introduce new API')
good_tag = Tool(root).check_tag('v1.0.0')
try:
    Tool(root).check_tag('v9.9.9')
except ValueError as exc:
    wrong_tag = str(exc)
result = {'patch': patch, 'minor': minor, 'major': major,
          'valid_release': good_tag, 'rejected_release': wrong_tag}

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
