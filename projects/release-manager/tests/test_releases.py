import pytest

from application.releases import Releases, parse


@pytest.fixture
def app(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="sample"\nversion="1.2.3"\n')
    return Releases(tmp_path)


@pytest.mark.parametrize("version", ["1.2", "01.2.3", "-1.2.3", "1.2.3.4", "v1.2.3"])
def test_invalid_version(version):
    with pytest.raises(ValueError):
        parse(version)


@pytest.mark.parametrize("part,expected", [("MAJOR", "2.0.0"), ("MINOR", "1.3.0"), ("PATCH", "1.2.4")])
def test_bump(app, part, expected):
    assert app.bump(part, "New release")["version"] == expected
    assert app.current() == expected


def test_duplicate_release(app):
    app.register("1.2.3", "Initial")
    with pytest.raises(ValueError, match="already"):
        app.register("1.2.3", "Again")


def test_decrease(app):
    with pytest.raises(ValueError, match="decrease"):
        app.register("1.0.0", "Older")


def test_good_tag(app):
    assert app.check_tag("v1.2.3")["valid"]


@pytest.mark.parametrize("tag", [None, "", "v1.2.4", "1.2.3", "vbad"])
def test_bad_tag(app, tag):
    with pytest.raises(ValueError):
        app.check_tag(tag)


def test_changelog(app):
    app.bump("PATCH", "Fix validation")
    assert "1.2.4" in (app.root / "CHANGELOG.md").read_text()


def test_regular_operations_need_no_tag(app):
    assert app.current() == "1.2.3"
