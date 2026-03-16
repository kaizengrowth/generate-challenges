"""
Seed the database with three realistic fake students for demo purposes.

Students
--------
alice   — finished the Stack challenge, moved on to LinkedList, almost done
bob     — mid-way through Stack, clearly struggling with edge cases
carlos  — just started, first test run was 0/8

Usage
-----
    python seed.py              # seed with defaults
    python seed.py --cohort my-cohort   # custom cohort id
    python seed.py --reset      # drop and recreate the db first
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta

import db


COHORT_ID = "demo-cohort"

CHALLENGES = ["Stack", "LinkedList", "BinarySearch"]


def _ts(minutes_ago: int) -> str:
    t = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return t.isoformat()


def _event(
    student_id: str,
    challenge: str,
    passed: int,
    total: int,
    minutes_ago: int,
    results: list[dict] | None = None,
) -> None:
    if results is None:
        # Auto-generate results matching passed/total
        results = []
        test_names = _test_names(challenge, total)
        for i, name in enumerate(test_names):
            status = "passed" if i < passed else "failed"
            error = None if status == "passed" else _common_error(challenge, name)
            results.append({"name": name, "status": status, "duration": 8 + i * 3, "error": error})

    payload = {
        "type": "test_run",
        "timestamp": _ts(minutes_ago),
        "sessionId": f"seed-{student_id}-{minutes_ago}",
        "studentId": student_id,
        "cohortId": COHORT_ID,
        "challenge": challenge,
        "testFile": f"src/{challenge}/{challenge}.test.ts",
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "duration": sum(r["duration"] for r in results),
        },
    }

    db.insert_event(
        cohort_id   = COHORT_ID,
        student_id  = student_id,
        session_id  = payload["sessionId"],
        event_type  = "test_run",
        challenge   = challenge,
        passed      = passed,
        total       = total,
        duration_ms = payload["summary"]["duration"],
        payload     = payload,
        received_at = _ts(minutes_ago),
    )


def _test_names(challenge: str, total: int) -> list[str]:
    banks = {
        "Stack": [
            "should create an empty stack",
            "should report size as 0 when empty",
            "should push items onto the stack",
            "should return the top item with peek",
            "should pop items in LIFO order",
            "should return undefined when popping empty stack",
            "should return undefined when peeking empty stack",
            "should report isEmpty correctly after push and pop",
        ],
        "LinkedList": [
            "should create an empty list",
            "should append a node to the list",
            "should prepend a node to the list",
            "should find a node by value",
            "should delete a node by value",
            "should return null when deleting non-existent value",
            "should traverse the list in order",
            "should report length correctly",
        ],
        "BinarySearch": [
            "should return -1 for an empty array",
            "should find an element at the start",
            "should find an element at the end",
            "should find an element in the middle",
            "should return -1 when element not present",
            "should handle single-element array (found)",
            "should handle single-element array (not found)",
            "should work on large sorted arrays",
        ],
    }
    names = banks.get(challenge, [f"test {i+1}" for i in range(total)])
    return names[:total]


def _common_error(challenge: str, test_name: str) -> str:
    errors = {
        "should return undefined when popping empty stack":
            "AssertionError: expected null to be undefined",
        "should return undefined when peeking empty stack":
            "AssertionError: expected null to be undefined",
        "should report isEmpty correctly after push and pop":
            "AssertionError: expected false to be true",
        "should return null when deleting non-existent value":
            "TypeError: Cannot read properties of undefined (reading 'next')",
        "should return -1 when element not present":
            "AssertionError: expected 3 to equal -1",
    }
    return errors.get(test_name, "AssertionError: expected values to match")


def seed_alice():
    """
    alice — finished Stack (all 8/8 after 4 attempts), now 6/8 into LinkedList.
    Story: strong student, got tripped up by null-vs-undefined but figured it out.
    """
    # Stack journey — 4 attempts over ~45 minutes
    _event("alice", "Stack",      0, 8, minutes_ago=90)
    _event("alice", "Stack",      3, 8, minutes_ago=78)
    _event("alice", "Stack",      6, 8, minutes_ago=65)
    _event("alice", "Stack",      8, 8, minutes_ago=58)  # completed

    # LinkedList — started 30 min ago, making good progress
    _event("alice", "LinkedList", 0, 8, minutes_ago=45)
    _event("alice", "LinkedList", 4, 8, minutes_ago=33)
    _event("alice", "LinkedList", 6, 8, minutes_ago=18)


def seed_bob():
    """
    bob — stuck on Stack, 5 attempts, best is 5/8, keeps failing the empty-stack tests.
    Story: understands basic push/pop but misses boundary conditions.
    """
    _event("bob", "Stack", 0, 8, minutes_ago=85)
    _event("bob", "Stack", 2, 8, minutes_ago=74)
    _event("bob", "Stack", 4, 8, minutes_ago=62)
    _event("bob", "Stack", 5, 8, minutes_ago=50)
    _event("bob", "Stack", 5, 8, minutes_ago=22)  # still stuck at 5/8


def seed_carlos():
    """
    carlos — just started, one attempt 10 minutes ago, 0/8.
    Story: typical starting point; everything is red.
    """
    _event("carlos", "Stack", 0, 8, minutes_ago=10)


def main():
    global COHORT_ID
    parser = argparse.ArgumentParser(description="Seed the telemetry database for demo.")
    parser.add_argument("--cohort", default=COHORT_ID, help="Cohort ID to seed into")
    parser.add_argument("--reset", action="store_true", help="Delete the database before seeding")
    args = parser.parse_args()

    COHORT_ID = args.cohort

    if args.reset:
        db_path = db.DB_PATH
        if db_path.exists():
            db_path.unlink()
            print(f"Deleted {db_path}")

    db.init_db()

    print(f"Seeding cohort '{COHORT_ID}'...")
    seed_alice()
    print("  ✓ alice  — Stack complete (8/8), LinkedList in progress (6/8)")
    seed_bob()
    print("  ✓ bob    — Stack in progress (5/8), stuck on edge cases")
    seed_carlos()
    print("  ✓ carlos — Stack just started (0/8)")

    print(f"\nDone. Database: {db.DB_PATH}")
    print(f"\nCheck it:")
    print(f"  curl http://localhost:8000/cohort/{COHORT_ID}")


if __name__ == "__main__":
    main()
