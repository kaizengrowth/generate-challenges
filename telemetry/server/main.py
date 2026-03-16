"""
Telemetry ingest server.

Endpoints
---------
POST /events
    Receive a telemetry event from a student's challenge repo.
    Writes to SQLite and broadcasts to any SSE listeners on that cohort.

GET /cohort/{cohort_id}
    Return aggregated data for all students in a cohort.

GET /cohort/{cohort_id}/student/{student_id}
    Return full test history for one student.

GET /stream/{cohort_id}
    Server-Sent Events stream — pushes a message whenever a new event
    arrives for the given cohort. Connect once; stay connected.

GET /health
    Liveness check.

Run
---
    cd telemetry/server
    uvicorn main:app --reload --port 8000
"""

import asyncio
import json
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import db


# ---------------------------------------------------------------------------
# SSE broker — in-process pub/sub, one queue per cohort
# ---------------------------------------------------------------------------

class SSEBroker:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, cohort_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues[cohort_id].append(q)
        return q

    def unsubscribe(self, cohort_id: str, q: asyncio.Queue) -> None:
        try:
            self._queues[cohort_id].remove(q)
        except ValueError:
            pass

    async def publish(self, cohort_id: str, message: dict) -> None:
        dead = []
        for q in self._queues[cohort_id]:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(cohort_id, q)


broker = SSEBroker()


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(
    title="Challenge Telemetry Server",
    description="Receives learning events from student challenge repos and serves cohort analytics.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class TestResult(BaseModel):
    name: str
    status: str  # "passed" | "failed" | "skipped"
    duration: int = 0
    error: str | None = None


class TestSummary(BaseModel):
    total: int
    passed: int
    failed: int
    duration: int


class TelemetryEvent(BaseModel):
    type: str = Field(..., description="'test_run' or 'ai_evaluation'")
    timestamp: str
    sessionId: str
    studentId: str | None = None
    cohortId: str | None = None
    challenge: str
    testFile: str | None = None
    results: list[TestResult] = []
    summary: TestSummary | None = None
    evaluation: dict | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "time": _now()}


@app.post("/events")
async def ingest_event(event: TelemetryEvent, request: Request):
    """
    Receive a telemetry event.

    cohort_id and student_id can be supplied in the JSON body
    or as query parameters (useful when testing with curl).
    """
    params = dict(request.query_params)
    cohort_id  = event.cohortId  or params.get("cohort_id",  "default")
    student_id = event.studentId or params.get("student_id", "anonymous")

    passed      = event.summary.passed      if event.summary else 0
    total       = event.summary.total       if event.summary else 0
    duration_ms = event.summary.duration    if event.summary else 0
    received_at = _now()

    row_id = db.insert_event(
        cohort_id   = cohort_id,
        student_id  = student_id,
        session_id  = event.sessionId,
        event_type  = event.type,
        challenge   = event.challenge,
        passed      = passed,
        total       = total,
        duration_ms = duration_ms,
        payload     = event.model_dump(),
        received_at = received_at,
    )

    # Broadcast to SSE listeners
    broadcast = {
        "id":         row_id,
        "type":       event.type,
        "studentId":  student_id,
        "cohortId":   cohort_id,
        "challenge":  event.challenge,
        "passed":     passed,
        "total":      total,
        "receivedAt": received_at,
    }
    await broker.publish(cohort_id, broadcast)

    return {"ok": True, "id": row_id, "cohortId": cohort_id, "studentId": student_id}


@app.get("/cohort/{cohort_id}")
def cohort_summary(cohort_id: str):
    """Aggregated view of all students in a cohort."""
    students  = db.get_cohort_students(cohort_id)
    heatmap   = db.get_challenge_heatmap(cohort_id)

    completed = sum(
        1 for s in students
        if s["latest_passed"] is not None and s["latest_passed"] == s["latest_total"]
    )

    return {
        "cohortId":        cohort_id,
        "studentCount":    len(students),
        "completedCount":  completed,
        "students":        students,
        "challengeHeatmap": heatmap,
        "generatedAt":     _now(),
    }


@app.get("/cohort/{cohort_id}/student/{student_id}")
def student_detail(cohort_id: str, student_id: str):
    """Full test-run history for one student."""
    history = db.get_student_history(cohort_id, student_id)
    if not history:
        raise HTTPException(status_code=404, detail="Student not found in this cohort")

    return {
        "cohortId":  cohort_id,
        "studentId": student_id,
        "runs":      len(history),
        "history":   history,
    }


@app.get("/stream/{cohort_id}")
async def event_stream(cohort_id: str):
    """
    Server-Sent Events stream for a cohort.

    On connect: replays the 20 most recent events so the dashboard
    has something to show immediately.
    On new event: pushes within milliseconds of receipt.
    """
    queue = broker.subscribe(cohort_id)

    async def generator():
        # Replay recent history so a freshly-opened dashboard isn't empty
        recent = db.get_recent_events(cohort_id, limit=20)
        for event in recent:
            yield _sse(event, event_id="history")

        yield _sse({"type": "connected", "cohortId": cohort_id})

        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield _sse(message)
                except asyncio.TimeoutError:
                    # Keepalive ping so proxies don't close the connection
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            broker.unsubscribe(cohort_id, queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no",   # nginx: disable buffering
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sse(data: dict, event_id: str | None = None) -> str:
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)
