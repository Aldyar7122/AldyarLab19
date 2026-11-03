"""Configurable repository audit. Findings are not a certification."""

import html
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

from .common import now, write_json

DEFAULT_RULES = {
    "required_files": ["README.md", "CHANGELOG.md", "pyproject.toml"],
    "min_commits": 5,
    "require_git": True,
    "require_ci": True,
}


class Auditor:
    def __init__(self, path):
        self.root = Path(path).resolve()

    def audit(self, rules=None, output=None):
        findings = []

        def issue(rule, severity, message):
            findings.append({"rule": rule, "severity": severity, "message": message})

        try:
            settings = DEFAULT_RULES.copy()
            if rules:
                custom = json.loads(Path(rules).read_text(encoding="utf-8"))
                if not isinstance(custom, dict) or custom.keys() - DEFAULT_RULES.keys():
                    raise ValueError("unknown rules or non-object configuration")
                settings.update(custom)
            if not isinstance(settings["required_files"], list) or not all(
                isinstance(v, str) for v in settings["required_files"]
            ):
                raise ValueError("required_files must be an array of paths")
            if type(settings["min_commits"]) is not int or settings["min_commits"] < 0:
                raise ValueError("min_commits must be a non-negative integer")
            if type(settings["require_git"]) is not bool or type(settings["require_ci"]) is not bool:
                raise ValueError("require_git and require_ci must be booleans")
            for file in settings["required_files"]:
                candidate = (self.root / file).resolve()
                if not candidate.is_relative_to(self.root):
                    raise ValueError("required file path escapes project")
                if not candidate.is_file():
                    issue("required_files", "error", f"missing {file}")
                elif not candidate.stat().st_size:
                    issue("required_files", "warning", f"empty {file}")
            try:
                version = tomllib.loads((self.root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
                    "version"
                ]
                if not isinstance(version, str) or not re.fullmatch(
                    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version
                ):
                    raise ValueError("invalid numeric SemVer")
            except (OSError, KeyError, TypeError, ValueError) as exc:
                issue("version", "error", f"invalid or missing package version: {exc}")
            if settings["require_ci"]:
                workflow = self.root / ".github" / "workflows"
                files = list(workflow.glob("*.yml")) + list(workflow.glob("*.yaml"))
                if not files:
                    issue("ci", "error", "missing CI workflow")
                elif not any(
                    "jobs:" in f.read_text(encoding="utf-8") and "steps:" in f.read_text(encoding="utf-8")
                    for f in files
                ):
                    issue("ci", "error", "workflow lacks jobs or steps")
            if settings["require_git"]:
                if not (self.root / ".git").exists():
                    issue("git", "error", "missing Git repository")
                else:
                    git = shutil.which("git")
                    if not git:
                        issue("git", "error", "git executable unavailable")
                    else:
                        run = subprocess.run(
                            [git, "-C", str(self.root), "rev-list", "--count", "HEAD"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if run.returncode or not run.stdout.strip().isdigit():
                            issue("git", "error", "Git history unavailable")
                        elif int(run.stdout) < settings["min_commits"]:
                            issue("commit_count", "error", f"need at least {settings['min_commits']} commits")
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            issue("rules", "critical", f"invalid audit configuration or unreadable file: {exc}")
        result = {
            "time": now(),
            "project": str(self.root),
            "passed": not any(f["severity"] in {"error", "critical"} for f in findings),
            "findings": findings,
            "scope": "internal rules; not ISO certification",
        }
        if output:
            write_json(str(output) + ".json", result)
            rows = "".join(
                "<tr>"
                + "".join(f"<td>{html.escape(str(f[k]))}</td>" for k in ("rule", "severity", "message"))
                + "</tr>"
                for f in findings
            )
            Path(str(output) + ".html").write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8"><title>Configuration audit</title>'
                "<style>body{font:16px Arial;margin:40px}td,th{padding:10px;border:1px solid #bbb}table{border-collapse:collapse}</style>"
                f"<h1>Configuration audit</h1><p>Passed: {result['passed']}</p><p>{html.escape(str(self.root))}</p>"
                "<table><tr><th>Rule</th><th>Severity</th><th>Finding</th></tr>"
                + rows
                + "</table><p>Internal project rules only. This report is not ISO certification.</p></html>",
                encoding="utf-8",
            )
        return result
