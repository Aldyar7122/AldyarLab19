from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
for project in sorted((root / 'projects').iterdir()):
    if not (project / 'pyproject.toml').exists():
        continue
    print("CHECK", project.name, flush=True)
    for command in ([sys.executable, '-m', 'ruff', 'check', '.'], [sys.executable, '-m', 'pytest', '-v']):
        subprocess.run(command, cwd=project, check=True)
    if project.name == 'configuration-auditor':
        # Audit the monorepo root because exported projects do not contain nested .git directories.
        env = dict(os.environ, PYTHONPATH=str(project / 'src'))
        subprocess.run([sys.executable, '-m', 'application', '--store', str(root), 'audit'], cwd=project, env=env, check=True)
    if project.name == 'scm-platform':
        subprocess.run([sys.executable, '-m', 'build', '--no-isolation'], cwd=project, check=True)
