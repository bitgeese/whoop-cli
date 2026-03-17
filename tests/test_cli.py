from typer.testing import CliRunner

from whoop_cli.cli import app, resolve_period

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "whoop" in result.output.lower()


def test_auth_status_not_authenticated(monkeypatch):
    monkeypatch.setattr("whoop_cli.auth.get_access_token", lambda: None)
    result = runner.invoke(app, ["auth", "status"])
    assert "Not authenticated" in result.output


def test_resolve_period_today():
    start, end = resolve_period("today")
    assert start.hour == 0
    assert start.minute == 0


def test_resolve_period_week():
    start, end = resolve_period("week")
    diff = end - start
    assert diff.days >= 6


def test_resolve_period_invalid():
    import typer
    import pytest

    with pytest.raises(typer.BadParameter):
        resolve_period("invalid")
