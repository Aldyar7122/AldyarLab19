import pytest

from application.changes import Tracker


@pytest.fixture
def app(tmp_path):
    tool = Tracker(tmp_path / "changes.db")
    yield tool
    tool.close()


def add(app, id="CR-001"):
    return app.add(id, "Aldyar", "feature", "Add a report")


def test_add(app):
    assert add(app)["status"] == "planned"


def test_duplicate(app):
    add(app)
    with pytest.raises(ValueError, match="duplicate"):
        add(app)


def test_invalid_status(app):
    add(app)
    with pytest.raises(ValueError):
        app.transition("CR-001", "unknown")


def test_cannot_skip(app):
    add(app)
    with pytest.raises(ValueError):
        app.transition("CR-001", "completed", "a" * 40)


def test_lifecycle(app):
    add(app)
    app.transition("CR-001", "in_progress")
    row = app.transition("CR-001", "completed", "a" * 40)
    assert row["commit_hash"] == "a" * 40
    assert len(app.history("CR-001")) == 3


def test_filter(app):
    add(app)
    app.add("CR-002", "Other", "fix", "Correct error")
    assert len(app.list(author="Aldyar", kind="feature", status="planned")) == 1


def test_report(app, tmp_path):
    add(app)
    assert len(app.report(tmp_path / "out.json")["changes"]) == 1
    assert (tmp_path / "out.json").exists()


def test_restart(app):
    add(app)
    other = Tracker(app.db.execute("PRAGMA database_list").fetchone()[2])
    assert other.list()[0]["id"] == "CR-001"
    other.close()


def test_bad_commit(app):
    add(app)
    app.transition("CR-001", "in_progress")
    with pytest.raises(ValueError):
        app.transition("CR-001", "completed", "bad")
