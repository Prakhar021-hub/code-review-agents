from code_review_agents.models import Finding
from code_review_agents.orchestrator import dedupe
from code_review_agents.parsing import parse_findings


def test_parses_well_formed_lines():
    text = (
        "- [HIGH] line 7: Division by zero. Fix: check length.\n"
        "- [LOW] line 3: Missing docstring. Fix: add one."
    )
    findings = parse_findings("bug_reviewer", text)

    assert len(findings) == 2
    assert findings[0].severity == "HIGH"
    assert findings[0].line == 7
    assert findings[0].source == "bug_reviewer"
    assert "Division by zero" in findings[0].description


def test_no_issues_found_gives_empty_list():
    assert parse_findings("bug_reviewer", "No issues found.") == []


def test_ignores_chatty_lines_around_findings():
    text = "Here is my review:\n- [MEDIUM] line 5: Unused variable. Fix: remove it.\nHope this helps!"
    findings = parse_findings("style_reviewer", text)

    assert len(findings) == 1
    assert findings[0].line == 5


def test_severity_is_case_insensitive():
    findings = parse_findings("x", "- [high] line 2: Problem. Fix: fix it.")
    assert findings[0].severity == "HIGH"


def test_dedupe_keeps_most_severe_for_same_reviewer_and_line():
    findings = [
        Finding("bug_reviewer", "LOW", 7, "minor"),
        Finding("bug_reviewer", "HIGH", 7, "major"),
    ]
    result = dedupe(findings)

    assert len(result) == 1
    assert result[0].severity == "HIGH"


def test_dedupe_keeps_same_line_from_different_reviewers():
    findings = [
        Finding("bug_reviewer", "HIGH", 11, "a"),
        Finding("security_reviewer", "HIGH", 11, "b"),
    ]
    assert len(dedupe(findings)) == 2