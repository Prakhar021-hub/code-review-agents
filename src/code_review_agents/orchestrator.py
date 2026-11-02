import logging

from langsmith import traceable

import sqlite3

from code_review_agents.storage import save_run

from code_review_agents.agents.reviewers import ALL_REVIEWERS
from code_review_agents.llm import ask
from code_review_agents.models import SEVERITY_ORDER, Finding
from code_review_agents.parsing import parse_findings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """You are a senior engineer writing the top of a code review.
You will get a list of findings. Write a 2-3 sentence summary for the author:
the overall impression and what to fix first.
Only mention issues that appear in the list. Do not invent new ones."""


def dedupe(findings: list[Finding]) -> list[Finding]:
    """If one reviewer reports the same line twice, keep the most severe."""
    best = {}
    for f in findings:
        key = (f.source, f.line)
        if key not in best or SEVERITY_ORDER[f.severity] < SEVERITY_ORDER[best[key].severity]:
            best[key] = f
    return list(best.values())


@traceable(run_type="chain", name="run_reviewer")
def run_reviewer(agent, code: str) -> list[Finding]:
    """Run one reviewer. If its reply can't be parsed, try once more."""
    for attempt in (1, 2):
        text = agent.review(code)
        logger.debug("%s raw reply:\n%s", agent.name, text)
        findings = parse_findings(agent.name, text)
        if findings or "no issues found" in text.lower():
            return findings
        logger.warning("%s gave an unreadable reply (attempt %d)", agent.name, attempt)
    return []


@traceable(run_type="chain", name="review_code")
def review_code(code: str) -> list[Finding]:
    """Run every reviewer, then dedupe and rank their findings."""
    findings = []
    for agent in ALL_REVIEWERS:
        try:
            findings.extend(run_reviewer(agent, code))
        except Exception as error:
            logger.warning("%s failed (%s). Continuing without it.", agent.name, error)

    findings = dedupe(findings)
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.line))
    return findings


@traceable(run_type="chain", name="build_report")
def build_report(findings: list[Finding]) -> str:
    """Format findings and add a short model-written summary on top."""
    if not findings:
        return "No issues found."
    listing = "\n".join(
        f"[{f.severity}] line {f.line} ({f.source}): {f.description}"
        for f in findings
    )
    summary = ask(SUMMARY_PROMPT, listing)
    return f"{summary}\n\n{listing}"


@traceable(run_type="chain", name="code_review_run")
def run_full_review(code: str, source_name: str = "unnamed") -> str:
    """The entry point: review the code, save the run, return the report."""
    findings = review_code(code)
    report = build_report(findings)
    try:
        run_id = save_run(source_name, code, report, findings)
        logger.info("Saved as review #%d", run_id)
    except sqlite3.Error as error:
        logger.warning("Could not save this review (%s). Showing it anyway.", error)
    return report