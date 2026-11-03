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
from application.auditor import Auditor as Tool
data = root / '.data' / ('demo-' + uuid.uuid4().hex[:8])
data.mkdir(parents=True)
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
def put_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
audit_root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=root, text=True).strip())
app = Tool(audit_root)
good = app.audit(output=evidence / 'compliant-audit')
bad = data / 'noncompliant'
bad.mkdir()
(bad / 'pyproject.toml').write_text('[project]\nversion="01.0.0"', encoding='utf-8')
bad_result = Tool(bad).audit(output=evidence / 'noncompliant-audit')
result = {'compliant_passed': good['passed'], 'noncompliant_passed': bad_result['passed'],
          'noncompliant_findings': bad_result['findings']}

put_json(evidence / 'demo.json', result)
print(json.dumps(result, ensure_ascii=False, indent=2))
