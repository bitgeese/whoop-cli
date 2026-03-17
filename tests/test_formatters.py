import json

from whoop_cli.formatters import format_csv, format_json, format_markdown, ms_to_human, pct
from whoop_cli.models import Profile, Recovery, RecoveryScore


def test_ms_to_human():
    assert ms_to_human(28800000) == "8h 00m"
    assert ms_to_human(5400000) == "1h 30m"
    assert ms_to_human(300000) == "5m"
    assert ms_to_human(None) == "-"


def test_pct():
    assert pct(85.0) == "85%"
    assert pct(None) == "-"


def test_format_json_model():
    p = Profile(user_id=1, email="test@example.com", first_name="Test", last_name="User")
    result = format_json(p)
    data = json.loads(result)
    assert data["email"] == "test@example.com"


def test_format_json_list():
    items = [
        Profile(user_id=1, email="a@b.com", first_name="A", last_name="B"),
        Profile(user_id=2, email="c@d.com", first_name="C", last_name="D"),
    ]
    result = format_json(items)
    data = json.loads(result)
    assert len(data) == 2


def test_format_csv_model():
    p = Profile(user_id=1, email="test@example.com", first_name="Test", last_name="User")
    result = format_csv(p)
    assert "email" in result
    assert "test@example.com" in result


def test_format_csv_nested():
    r = Recovery(
        cycle_id=1, sleep_id=1, user_id=1,
        score_state="SCORED",
        score=RecoveryScore(recovery_score=78.0, hrv_rmssd_milli=45.3),
    )
    result = format_csv(r)
    assert "score.recovery_score" in result
    assert "78.0" in result


def test_format_markdown_single():
    p = Profile(user_id=1, email="test@example.com", first_name="Test", last_name="User")
    result = format_markdown(p, title="Profile")
    assert "Profile" in result
    assert "test@example.com" in result


def test_format_markdown_list():
    items = [
        Profile(user_id=1, email="a@b.com", first_name="A", last_name="B"),
        Profile(user_id=2, email="c@d.com", first_name="C", last_name="D"),
    ]
    result = format_markdown(items)
    assert "a@b.com" in result
    assert "c@d.com" in result
