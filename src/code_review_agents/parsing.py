import re

from code_review_agents.models import Finding
from langsmith import traceable

PATTERN = re.compile(
    r"-\s*\[(HIGH|MEDIUM|LOW)\]\s*line\s*(\d+):\s*(.+)", re.IGNORECASE
)


@traceable(run_type="parser", name="parse_findings")
def parse_findings(source: str, text: str) -> list[Finding]:
    """Turn a reviewer's text reply into Finding objects.

    Lines that don't match the expected format (like "No issues found.")
    are skipped instead of crashing the program.
    """
    findings = []
    for raw_line in text.splitlines():
        match = PATTERN.search(raw_line)
        if match:
            findings.append(
                Finding(
                    source=source,
                    severity=match.group(1).upper(),
                    line=int(match.group(2)),
                    description=match.group(3).strip(),
                )
            )
    return findings