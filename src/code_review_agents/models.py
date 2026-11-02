from dataclasses import dataclass

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


@dataclass
class Finding:
    """One issue reported by one reviewer."""

    source: str
    severity: str
    line: int
    description: str