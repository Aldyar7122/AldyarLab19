import pytest

from application.scanner import Scanner


@pytest.fixture
def app(tmp_path):
    return Scanner(tmp_path)


def base(app, id="BL-001", **kwargs):
    return app.baseline(id, "Reviewer", "a" * 40, **kwargs)


def test_empty(app):
    assert app.scan() == []


def test_hash_and_relative(app):
    path = app.root / "src" / "main.py"
    path.parent.mkdir()
    path.write_text("hello")
    row = app.scan()[0]
    assert row["path"] == "src/main.py" and len(row["sha256"]) == 64 and row["size"] == 5


def test_content_change(app):
    file = app.root / "a.txt"
    file.write_text("one")
    base(app)
    file.write_text("two")
    assert app.compare("BL-001")["changed"] == ["a.txt"]


def test_added_removed(app):
    file = app.root / "old"
    file.write_text("a")
    base(app)
    file.unlink()
    (app.root / "new").write_text("b")
    result = app.compare("BL-001")
    assert result["added"] == ["new"] and result["removed"] == ["old"]


@pytest.mark.parametrize("folder", [".git", "__pycache__", "venv", ".venv"])
def test_exclusions(app, folder):
    path = app.root / folder
    path.mkdir()
    (path / "secret").write_text("hidden")
    assert app.scan() == []


def test_custom_exclusion(app):
    (app.root / "a.log").write_text("log")
    assert app.scan(["*.log"]) == []


def test_missing_baseline(app):
    with pytest.raises(ValueError, match="does not exist"):
        app.compare("missing")


def test_immutable(app):
    first = base(app)
    with pytest.raises(ValueError, match="immutable"):
        base(app)
    assert app.load("BL-001") == first


def test_self_excluded(app):
    base(app)
    assert app.scan() == []
    assert not app.compare("BL-001")["added"]


def test_two_snapshots(app):
    base(app)
    (app.root / "file").write_text("content")
    second = base(app, "BL-002", previous="BL-001")
    assert second["previous"] == "BL-001"
    assert app.compare("BL-001", "BL-002")["added"] == ["file"]
