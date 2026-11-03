import sqlite3

import pytest

from application.platform import Platform


@pytest.fixture
def app(tmp_path):
    tool = Platform(tmp_path / "scm.db")
    tool.project("P1", "SCM example")
    tool.item("P1", "CI-001", "main.py", "1.0", "print(1)")
    yield tool
    tool.close()


def request(app, id="CR-001", version="1.1"):
    return app.request(id, "P1", "CI-001", version, "print(2)", "Improve output")


def applied(app):
    request(app)
    app.decide("CR-001", True, "Reviewer", "Approved after review")
    return app.apply("CR-001", "a" * 40, "test_full_scenario")


def test_project(app):
    assert len(app.report()["projects"]) == 1


def test_duplicate_project(app):
    with pytest.raises(ValueError):
        app.project("P1", "Again")


def test_item_registration(app):
    assert len(app.items("P1")[0]["sha256"]) == 64


def test_duplicate_item(app):
    with pytest.raises(ValueError):
        app.item("P1", "CI-001", "main.py", "1.0", "other")


def test_request(app):
    assert request(app)["status"] == "pending"


def test_unapproved_change(app):
    request(app)
    with pytest.raises(ValueError, match="approved"):
        app.apply("CR-001", "a" * 40, "test")


def test_approve(app):
    request(app)
    assert app.decide("CR-001", True, "Reviewer", "OK")["status"] == "approved"


def test_reject(app):
    request(app)
    app.decide("CR-001", False, "Reviewer", "Insufficient evidence")
    with pytest.raises(ValueError):
        app.apply("CR-001", "a" * 40, "test")


def test_apply_and_versions(app):
    applied(app)
    assert app.items("P1")[0]["version"] == "1.1"
    assert len(app.report()["item_versions"]) == 2


def test_apply_twice(app):
    applied(app)
    with pytest.raises(ValueError):
        app.apply("CR-001", "a" * 40, "test")


def test_baseline(app):
    row = app.baseline("BL-001", "P1", "Reviewer")
    assert len(row["items"]) == 1


def test_baseline_immutable(app):
    app.baseline("BL-001", "P1", "Reviewer")
    with pytest.raises(ValueError):
        app.baseline("BL-001", "P1", "Reviewer")
    with pytest.raises(sqlite3.IntegrityError), app.db:
        app.db.execute("UPDATE baselines SET approver='Other' WHERE id='BL-001'")


def test_baseline_compare(app):
    app.baseline("BL-001", "P1", "Reviewer")
    applied(app)
    app.baseline("BL-002", "P1", "Reviewer", "BL-001")
    assert app.compare("BL-001", "BL-002")["changed"] == ["CI-001"]


def test_release(app):
    app.baseline("BL-001", "P1", "Reviewer")
    assert app.release("P1", "1.0.0", "BL-001")["baseline"] == "BL-001"


def test_cross_project_release(app):
    app.baseline("BL-001", "P1", "Reviewer")
    app.project("P2", "Other")
    with pytest.raises(ValueError):
        app.release("P2", "1.0.0", "BL-001")


def test_history_and_report(app, tmp_path):
    applied(app)
    result = app.report(tmp_path / "out.json")
    assert any(row["event"] == "change_applied" for row in result["history"])


def test_full_scenario(app):
    applied(app)
    app.baseline("BL-001", "P1", "Reviewer")
    app.release("P1", "1.0.0", "BL-001")
    report = app.report()
    assert report["requests"][0]["status"] == "applied" and len(report["releases"]) == 1


def test_restart(app):
    other = Platform(app.db.execute("PRAGMA database_list").fetchone()[2])
    assert len(other.items("P1")) == 1
    other.close()


def test_request_history(app):
    applied(app)
    assert [v["event"] for v in app.request_history("CR-001")] == ["change_requested", "decision", "change_applied"]


def test_baseline_history(app):
    app.baseline("BL-001", "P1", "Reviewer")
    assert app.baseline_history("P1")[0]["id"] == "BL-001"


def test_release_list(app):
    app.baseline("BL-001", "P1", "Reviewer")
    app.release("P1", "1.0.0", "BL-001")
    assert app.list_releases("P1")[0]["version"] == "1.0.0"


def test_baseline_delete_blocked(app):
    app.baseline("BL-001", "P1", "Reviewer")
    with pytest.raises(sqlite3.IntegrityError):
        with app.db:
            app.db.execute("DELETE FROM baselines WHERE id='BL-001'")
    assert app.get_baseline("BL-001")["items"]
