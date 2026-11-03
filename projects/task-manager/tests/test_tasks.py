import pytest

from application.conflict_demo import features
from application.tasks import Tasks


@pytest.fixture
def app(tmp_path):
    tool = Tasks(tmp_path / "tasks.db")
    yield tool
    tool.close()


def test_create_read(app):
    row = app.add("Implement filter", "Aldyar")
    assert app.get(row["id"])["title"] == "Implement filter"


def test_update(app):
    row = app.add("A", "Aldyar")
    assert app.update(row["id"], status="done")["status"] == "done"


def test_delete(app):
    row = app.add("A", "Aldyar")
    app.delete(row["id"])
    with pytest.raises(ValueError):
        app.get(row["id"])


def test_three_filters(app):
    app.add("A", "Aldyar", "high", "done")
    app.add("B", "Other", "low")
    assert len(app.list(assignee="Aldyar", priority="high", status="done")) == 1


def test_statistics(app):
    app.add("A", "Aldyar", status="done")
    app.add("B", "Aldyar")
    assert app.statistics() == {"total": 2, "done": 1, "completion_percent": 50}


def test_empty_statistics(app):
    assert app.statistics()["completion_percent"] == 0


@pytest.mark.parametrize("kwargs", [{"priority": "urgent"}, {"status": "wrong"}, {"title": ""}])
def test_validation(app, kwargs):
    args = {"title": "A", "assignee": "Aldyar", **kwargs}
    with pytest.raises(ValueError):
        app.add(**args)


def test_restart(app):
    app.add("A", "Aldyar")
    other = Tasks(app.db.execute("PRAGMA database_list").fetchone()[2])
    assert len(other.list()) == 1
    other.close()


def test_merge_preserves_functions(app):
    assert features() == ["tasks", "filter", "statistics"]
    app.add("A", "Aldyar", status="done")
    assert app.list(status="done") and app.statistics()["done"] == 1
