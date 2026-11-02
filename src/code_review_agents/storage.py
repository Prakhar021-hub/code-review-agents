import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from code_review_agents.models import Finding

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source_name TEXT NOT NULL,
    code TEXT NOT NULL,
    report TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    source TEXT NOT NULL,
    severity TEXT NOT NULL,
    line INTEGER NOT NULL,
    description TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    """Open the database, creating the tables the first time."""
    conn = sqlite3.connect(os.getenv("REVIEW_DB", "reviews.db"))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_run(
    source_name: str, code: str, report: str, findings: list[Finding]
) -> int:
    """Save one review and all its findings. Returns the new run's id."""
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(_connect()) as conn:
        with conn:  # commits if everything works, undoes it all if anything fails
            cursor = conn.execute(
                "INSERT INTO runs (created_at, source_name, code, report) "
                "VALUES (?, ?, ?, ?)",
                (created_at, source_name, code, report),
            )
            run_id = cursor.lastrowid
            conn.executemany(
                "INSERT INTO findings (run_id, source, severity, line, description) "
                "VALUES (?, ?, ?, ?, ?)",
                [(run_id, f.source, f.severity, f.line, f.description) for f in findings],
            )
    return run_id


def list_runs(limit: int = 10) -> list[sqlite3.Row]:
    """Most recent reviews first, with a count of findings for each."""
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT r.id, r.created_at, r.source_name, COUNT(f.id) AS finding_count "
            "FROM runs r LEFT JOIN findings f ON f.run_id = r.id "
            "GROUP BY r.id ORDER BY r.id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_run(run_id: int) -> sqlite3.Row | None:
    """Fetch one saved review, or None if the id doesn't exist."""
    with closing(_connect()) as conn:
        return conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ).fetchone()