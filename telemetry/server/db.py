"""
SQLite database layer for the telemetry server.

Schema
------
events      — one row per test_run or ai_evaluation event received
students    — one row per (cohort_id, student_id) pair, auto-upserted on first event
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent / "telemetry.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads during SSE
    return conn


@contextmanager
def db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT    NOT NULL,
                cohort_id   TEXT    NOT NULL,
                student_id  TEXT    NOT NULL,
                session_id  TEXT    NOT NULL,
                event_type  TEXT    NOT NULL,
                challenge   TEXT    NOT NULL,
                passed      INTEGER NOT NULL DEFAULT 0,
                total       INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                payload     TEXT    NOT NULL  -- full event JSON
            );

            CREATE INDEX IF NOT EXISTS idx_events_cohort   ON events (cohort_id);
            CREATE INDEX IF NOT EXISTS idx_events_student  ON events (cohort_id, student_id);
            CREATE INDEX IF NOT EXISTS idx_events_received ON events (received_at);

            CREATE TABLE IF NOT EXISTS students (
                cohort_id       TEXT NOT NULL,
                student_id      TEXT NOT NULL,
                first_seen_at   TEXT NOT NULL,
                last_active_at  TEXT NOT NULL,
                PRIMARY KEY (cohort_id, student_id)
            );
        """)


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

def insert_event(
    cohort_id: str,
    student_id: str,
    session_id: str,
    event_type: str,
    challenge: str,
    passed: int,
    total: int,
    duration_ms: int,
    payload: dict,
    received_at: str,
) -> int:
    with db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO events
                (received_at, cohort_id, student_id, session_id,
                 event_type, challenge, passed, total, duration_ms, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                received_at, cohort_id, student_id, session_id,
                event_type, challenge, passed, total, duration_ms,
                json.dumps(payload),
            ),
        )
        conn.execute(
            """
            INSERT INTO students (cohort_id, student_id, first_seen_at, last_active_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (cohort_id, student_id)
            DO UPDATE SET last_active_at = excluded.last_active_at
            """,
            (cohort_id, student_id, received_at, received_at),
        )
        return cursor.lastrowid


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def get_cohort_students(cohort_id: str) -> list[dict]:
    """Return all students in a cohort with their latest test summary."""
    with db() as conn:
        rows = conn.execute(
            """
            SELECT
                s.student_id,
                s.first_seen_at,
                s.last_active_at,
                COUNT(e.id)                                         AS total_runs,
                MAX(e.passed)                                       AS best_passed,
                (SELECT e2.total FROM events e2
                 WHERE e2.cohort_id = s.cohort_id
                   AND e2.student_id = s.student_id
                 ORDER BY e2.received_at DESC LIMIT 1)              AS latest_total,
                (SELECT e2.passed FROM events e2
                 WHERE e2.cohort_id = s.cohort_id
                   AND e2.student_id = s.student_id
                 ORDER BY e2.received_at DESC LIMIT 1)              AS latest_passed,
                (SELECT e2.challenge FROM events e2
                 WHERE e2.cohort_id = s.cohort_id
                   AND e2.student_id = s.student_id
                 ORDER BY e2.received_at DESC LIMIT 1)              AS latest_challenge
            FROM students s
            LEFT JOIN events e
                ON e.cohort_id = s.cohort_id AND e.student_id = s.student_id
                AND e.event_type = 'test_run'
            WHERE s.cohort_id = ?
            GROUP BY s.student_id
            ORDER BY s.last_active_at DESC
            """,
            (cohort_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_student_history(cohort_id: str, student_id: str) -> list[dict]:
    """Return all test_run events for one student, newest first."""
    with db() as conn:
        rows = conn.execute(
            """
            SELECT received_at, challenge, passed, total, duration_ms, payload
            FROM events
            WHERE cohort_id = ? AND student_id = ? AND event_type = 'test_run'
            ORDER BY received_at DESC
            """,
            (cohort_id, student_id),
        ).fetchall()
    return [dict(r) for r in rows]


def get_challenge_heatmap(cohort_id: str) -> list[dict]:
    """
    Per-challenge pass rate across the cohort.
    Shows which challenges students are struggling with most.
    """
    with db() as conn:
        rows = conn.execute(
            """
            SELECT
                challenge,
                COUNT(DISTINCT student_id)                   AS students_attempted,
                ROUND(AVG(CAST(passed AS REAL) / NULLIF(total, 0)) * 100, 1)
                                                             AS avg_pass_rate,
                SUM(CASE WHEN passed = total AND total > 0 THEN 1 ELSE 0 END)
                                                             AS completions
            FROM events
            WHERE cohort_id = ? AND event_type = 'test_run'
            GROUP BY challenge
            ORDER BY avg_pass_rate ASC
            """,
            (cohort_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_events(cohort_id: str, limit: int = 50) -> list[dict]:
    """Return the most recent events for SSE replay on connect."""
    with db() as conn:
        rows = conn.execute(
            """
            SELECT received_at, student_id, challenge, passed, total, event_type
            FROM events
            WHERE cohort_id = ?
            ORDER BY received_at DESC
            LIMIT ?
            """,
            (cohort_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]
