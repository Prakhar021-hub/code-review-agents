import pytest

from code_review_agents.models import Finding
from code_review_agents.storage import get_run, list_runs, save_run


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Give every test its own empty database, deleted afterward."""
    monkeypatch.setenv("REVIEW_DB", str(tmp_path / "test.db"))


def test_save_and_fetch_a_run():
    findings = [Finding("bug_reviewer", "HIGH", 7, "Division by zero")]
    run_id = save_run("a.py", "print(1)", "the report", findings)

    run = get_run(run_id)
    assert run["source_name"] == "a.py"
    assert run["report"] == "the report"


def test_history_lists_newest_first_with_finding_counts():
    save_run("first.py", "x", "r1", [])
    save_run("second.py", "y", "r2", [Finding("s", "LOW", 1, "d")])

    runs = list_runs()
    assert [r["source_name"] for r in runs] == ["second.py", "first.py"]
    assert runs[0]["finding_count"] == 1
    assert runs[1]["finding_count"] == 0


def test_missing_run_returns_none():
    assert get_run(999) is None