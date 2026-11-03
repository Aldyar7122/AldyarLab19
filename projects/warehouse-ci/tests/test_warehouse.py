import pytest

from application.warehouse import Warehouse


@pytest.fixture
def app(tmp_path):
    tool = Warehouse(tmp_path / "stock.db")
    tool.add("P1", "Notebook", "office")
    yield tool
    tool.close()


def test_create(app):
    assert app.get("P1")["stock"] == 0


def test_duplicate(app):
    with pytest.raises(ValueError, match="duplicate"):
        app.add("P1", "Other", "office")


def test_receipt(app):
    assert app.move("P1", "receipt", 10)["stock"] == 10


def test_writeoff(app):
    app.move("P1", "receipt", 10)
    assert app.move("P1", "writeoff", 4)["stock"] == 6


def test_insufficient(app):
    with pytest.raises(ValueError, match="insufficient"):
        app.move("P1", "writeoff", 1)
    assert app.get("P1")["stock"] == 0 and app.journal() == []


@pytest.mark.parametrize("quantity", [-1, 0, 1.5, True, "2"])
def test_invalid_quantity(app, quantity):
    with pytest.raises(ValueError):
        app.move("P1", "receipt", quantity)


def test_search_and_category(app):
    assert len(app.search("note", "office")) == 1
    assert app.search("note", "food") == []


def test_journal_and_report(app):
    app.move("P1", "receipt", 7)
    app.move("P1", "writeoff", 2)
    assert len(app.journal()) == 2 and app.report()["total_units"] == 5


def test_update(app):
    assert app.update("P1", "Paper", "supplies")["name"] == "Paper"


def test_delete_preserves_journal(app):
    app.move("P1", "receipt", 1)
    app.move("P1", "writeoff", 1)
    app.delete("P1")
    assert app.search() == [] and len(app.journal()) == 2


def test_delete_with_stock(app):
    app.move("P1", "receipt", 1)
    with pytest.raises(ValueError):
        app.delete("P1")


def test_restart(app):
    app.move("P1", "receipt", 3)
    other = Warehouse(app.db.execute("PRAGMA database_list").fetchone()[2])
    assert other.get("P1")["stock"] == 3
    other.close()
