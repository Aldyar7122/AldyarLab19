import pytest

from application.versions import Manager


@pytest.fixture
def app(tmp_path):
    return Manager(tmp_path / "docs")


def pair(app):
    app.create("lesson", "alpha\nbeta\n")
    a = app.save("lesson")
    app.edit("lesson", "alpha\ngamma\n")
    return a, app.save("lesson")


def test_save(app):
    app.create("a", "hello")
    row = app.save("a")
    assert row["content"] == "hello" and row["time"] and row["id"]


def test_compare(app):
    a, b = pair(app)
    diff = app.compare("lesson", a["id"], b["id"])["diff"]
    assert "-beta" in diff and "+gamma" in diff


def test_restore(app):
    a, b = pair(app)
    assert app.restore("lesson", a["id"])["content"] == "alpha\nbeta\n"


def test_missing_version(app):
    pair(app)
    with pytest.raises(ValueError, match="version"):
        app.restore("lesson", "missing")


def test_history_preserved(app):
    a, b = pair(app)
    app.restore("lesson", a["id"])
    assert [v["id"] for v in app.versions("lesson")][:2] == [a["id"], b["id"]]
    assert len(app.versions("lesson")) == 3


def test_restart(app):
    a, b = pair(app)
    assert len(Manager(app.path).versions("lesson")) == 2


@pytest.mark.parametrize("name", ["../escape", "", "/absolute", "a/b", "a\\b"])
def test_invalid_name(app, name):
    with pytest.raises(ValueError):
        app.create(name)


def test_duplicate_document(app):
    app.create("a")
    with pytest.raises(ValueError):
        app.create("a")
