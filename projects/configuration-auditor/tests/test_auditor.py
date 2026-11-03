import json
import subprocess

import pytest

from application.auditor import DEFAULT_RULES, Auditor


@pytest.fixture
def app(tmp_path):
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "CHANGELOG.md").write_text("# Changes")
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.0.0"\n')
    flow = tmp_path / ".github" / "workflows"
    flow.mkdir(parents=True)
    (flow / "ci.yml").write_text("jobs:\n  test:\n    steps: []\n")
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    for key, value in [("user.name", "Test"), ("user.email", "test@example.invalid")]:
        subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "Initial"], check=True, capture_output=True)
    return Auditor(tmp_path)


def rules(app, **kwargs):
    path = app.root / "rules.json"
    path.write_text(json.dumps({**DEFAULT_RULES, "min_commits": 1, **kwargs}))
    return str(path)


def test_compliant(app):
    assert app.audit(rules(app))["passed"]


@pytest.mark.parametrize("file", ["README.md", "CHANGELOG.md", "pyproject.toml"])
def test_missing_file(app, file):
    (app.root / file).unlink()
    assert not app.audit(rules(app))["passed"]


def test_missing_ci(app):
    (app.root / ".github/workflows/ci.yml").unlink()
    assert any(f["rule"] == "ci" for f in app.audit(rules(app))["findings"])


def test_invalid_version(app):
    (app.root / "pyproject.toml").write_text('[project]\nversion="01.0.0"')
    assert not app.audit(rules(app))["passed"]


def test_corrupt_toml(app):
    (app.root / "pyproject.toml").write_text("not [ TOML")
    assert not app.audit(rules(app))["passed"]


def test_commits(app):
    assert any(f["rule"] == "commit_count" for f in app.audit()["findings"])


def test_missing_git(tmp_path):
    assert any(f["rule"] == "git" for f in Auditor(tmp_path).audit()["findings"])


def test_corrupt_rules(app):
    path = app.root / "bad.json"
    path.write_text("{bad")
    assert app.audit(str(path))["findings"][0]["severity"] == "critical"


@pytest.mark.parametrize(
    "value", [{"min_commits": -1}, {"require_git": "yes"}, {"unknown": 2}, {"required_files": "../x"}]
)
def test_wrong_rules(app, value):
    path = app.root / "bad.json"
    path.write_text(json.dumps(value))
    assert not app.audit(str(path))["passed"]


def test_html_escape(app):
    report = app.audit(rules(app, required_files=["<script>.md"]), app.root / "report")
    assert not report["passed"]
    assert "&lt;script&gt;" in (app.root / "report.html").read_text()


def test_reports(app):
    app.audit(rules(app), app.root / "report")
    assert (app.root / "report.json").exists() and (app.root / "report.html").exists()
