import pytest

from application.traceability import Traceability


@pytest.fixture
def app(tmp_path):
    tool = Traceability(tmp_path / "registry.db")
    tool.project("P1", "Evidence project")
    tool.item("P1", "CI-001", "main.py", "1.0", "print(1)")
    (tmp_path / "main.py").write_text("print(1)")
    tool.root = tmp_path
    yield tool
    tool.close()


def change(app):
    app.request("CR-001", "P1", "CI-001", "1.1", "print(2)", "Change output")


def apply(app):
    change(app)
    app.decide("CR-001", True, "Reviewer", "Reviewed")
    app.apply("CR-001", "a" * 40, "test_chain")
    (app.root / "main.py").write_text("print(2)")


def test_item_registration(app):
    assert app.items("P1")[0]["id"] == "CI-001"


def test_version_change(app):
    apply(app)
    assert app.items("P1")[0]["version"] == "1.1"


def test_approval(app):
    change(app)
    assert app.decide("CR-001", True, "Reviewer", "OK")["status"] == "approved"


def test_rejection(app):
    change(app)
    assert app.decide("CR-001", False, "Reviewer", "No")["status"] == "rejected"


def test_unapproved_change(app):
    change(app)
    with pytest.raises(ValueError):
        app.apply("CR-001", "a" * 40, "test")


def test_baseline_valid(app):
    app.baseline("BL-001", "P1", "Reviewer")
    assert app.verify("BL-001", app.root)["passed"]


def test_baseline_detects_change(app):
    app.baseline("BL-001", "P1", "Reviewer")
    (app.root / "main.py").write_text("tampered")
    assert not app.verify("BL-001", app.root)["passed"]


def test_missing_file(app):
    app.baseline("BL-001", "P1", "Reviewer")
    (app.root / "main.py").unlink()
    assert not app.verify("BL-001", app.root)["passed"]


def test_chain(app):
    apply(app)
    app.baseline("BL-001", "P1", "Reviewer")
    chain = app.audit()["chains"][0]
    assert chain["request"] == "CR-001" and chain["commit"] == "a" * 40
    assert chain["baselines"] == ["BL-001"] and chain["test"] == "test_chain"


def test_incomplete_chain(app):
    apply(app)
    assert not app.audit()["passed"]


def test_matrix(app):
    rows = app.matrix()
    assert len(rows) == 7
    assert {"implemented", "partial", "not implemented"} <= {row["status"] for row in rows}


def test_report(app):
    app.audit(app.root / "audit.json")
    assert (app.root / "audit.json").exists()


def test_release(app):
    apply(app)
    app.baseline("BL-001", "P1", "Reviewer")
    assert app.release("P1", "1.0.0", "BL-001")["version"] == "1.0.0"
