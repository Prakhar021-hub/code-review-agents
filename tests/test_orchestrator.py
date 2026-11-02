import pytest

from code_review_agents import llm
from code_review_agents.orchestrator import run_full_review
from code_review_agents.storage import list_runs


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("REVIEW_DB", str(tmp_path / "test.db"))


def install_fake_model(monkeypatch, handler):
    """Replace the real model with `handler` everywhere our code uses it."""
    monkeypatch.setattr("code_review_agents.agents.base.ask", handler)
    monkeypatch.setattr("code_review_agents.orchestrator.ask", handler)


def default_fake(system_prompt, user_message, retries=3):
    if "senior engineer" in system_prompt:
        return "Fix the crash first."
    if "ONLY for bugs" in system_prompt:
        return "- [HIGH] line 7: Division by zero. Fix: check length."
    if "ONLY for security" in system_prompt:
        return "- [MEDIUM] line 11: SQL injection. Fix: use placeholders."
    return "- [LOW] line 3: Missing docstring. Fix: add one."


def test_full_review_ranks_findings_and_adds_summary(monkeypatch):
    install_fake_model(monkeypatch, default_fake)

    report = run_full_review("some code", source_name="demo.py")

    assert report.startswith("Fix the crash first.")
    assert report.index("[HIGH]") < report.index("[MEDIUM]") < report.index("[LOW]")


def test_review_is_saved_to_the_database(monkeypatch):
    install_fake_model(monkeypatch, default_fake)

    run_full_review("some code", source_name="demo.py")

    runs = list_runs()
    assert len(runs) == 1
    assert runs[0]["source_name"] == "demo.py"
    assert runs[0]["finding_count"] == 3


def test_one_failing_reviewer_does_not_stop_the_others(monkeypatch):
    def flaky(system_prompt, user_message, retries=3):
        if "ONLY for security" in system_prompt:
            raise RuntimeError("model is down")
        return default_fake(system_prompt, user_message)

    install_fake_model(monkeypatch, flaky)

    report = run_full_review("some code")

    assert "Division by zero" in report
    assert "SQL injection" not in report


def test_unreadable_reply_is_retried_once(monkeypatch):
    bug_calls = []

    def garbled_then_good(system_prompt, user_message, retries=3):
        if "ONLY for bugs" in system_prompt:
            bug_calls.append(1)
            if len(bug_calls) == 1:
                return "Sure! I think there might be some problems here."
        return default_fake(system_prompt, user_message)

    install_fake_model(monkeypatch, garbled_then_good)

    report = run_full_review("some code")

    assert len(bug_calls) == 2
    assert "Division by zero" in report


def test_clean_code_skips_the_summary_call(monkeypatch):
    summary_calls = []

    def all_clear(system_prompt, user_message, retries=3):
        if "senior engineer" in system_prompt:
            summary_calls.append(1)
        return "No issues found."

    install_fake_model(monkeypatch, all_clear)

    assert run_full_review("clean code") == "No issues found."
    assert summary_calls == []


def test_report_is_still_returned_if_saving_fails(monkeypatch, tmp_path):
    install_fake_model(monkeypatch, default_fake)
    # A database path inside a folder that doesn't exist makes saving fail
    monkeypatch.setenv("REVIEW_DB", str(tmp_path / "missing_folder" / "x.db"))

    report = run_full_review("some code")

    assert "Division by zero" in report


def test_call_budget_stops_runaway_loops(monkeypatch):
    monkeypatch.setattr(llm, "calls_made", llm.MAX_CALLS)

    with pytest.raises(RuntimeError, match="budget"):
        llm.ask("system", "user")