# System Architecture

This document describes the full architecture of the Challenge Generation Platform — the existing agentic generation pipeline, the planned telemetry system, and how they connect through a feedback loop.

---

## 1. Challenge Generation Pipeline

The existing system: a multi-agent Python pipeline that generates, validates, and iteratively refines testable coding challenge repos for bootcamp students.

```mermaid
flowchart LR
    CLI["🖥️  CLI\nmain.py\n─────────\n--topic\n--challenge\n--amend\n--resume-from"]

    subgraph rec ["Recommender"]
        Rec["💡 Recommender Agent\nTopic → 5–10 candidate\nchallenge ideas"]
        Sel["👩‍🏫 Instructor\npicks from Rich table"]
        Rec --> Sel
    end

    subgraph build ["Builder  (two-phase)"]
        Plan["📐 Planner\nfast model\n─────────\nClusters into repos\nPicks ecosystem\nLists files to generate"]
        Gen["🔨 Generator\nsonnet model\n─────────\nREADME · skeleton files\ntest files · config\nin batches of ≤ 3"]
        Plan --> Gen
    end

    subgraph validate ["Student Validation  (parallel)"]
        Expert["🧑‍💻 Expert Student\n─────────────────\nWhite-box: reviews tests\nWrites reference solution\nRuns real npm test / pytest\nBlack-box: reads test output"]
        Novice["🎓 Novice Student\n─────────────────\nWhite-box: reviews README\nScores clarity 1–5\nFlags confusion points"]
    end

    Loop{{"🔁 Issues?\n≤ 3 iterations"}}

    subgraph out ["Output"]
        Repos["📦 Challenge Repo\n─────────────────\nsrc/ skeleton files\ntests/ (start red)\nREADME.md\npackage.json / pom.xml / …\n.git/"]
        Ref["📋 Reference Solution\noutput/{topic}/\nreference_solutions/"]
        Log["📊 iteration_log.json\nbuild_manifest.json"]
    end

    subgraph kb ["Self-Learning"]
        KB["📚 knowledge_base/\n─────────────────\nlessons_learned.md\nchallenge_types/{slug}.md"]
    end

    CLI --> rec
    Sel --> build
    Gen --> validate
    Expert & Novice --> Loop
    Loop -->|"Yes — structured feedback\n→ back to Generator"| Gen
    Loop -->|"No — all clear"| out
    out -.->|"issues generalised\nby LLM after each run"| KB
    KB -.->|"injected into\nnext Builder prompt"| Plan

    style rec fill:#1e3a5f,color:#e8f4f8,stroke:#2d6a9f
    style build fill:#1e3a5f,color:#e8f4f8,stroke:#2d6a9f
    style validate fill:#1e3a5f,color:#e8f4f8,stroke:#2d6a9f
    style out fill:#1a3a2a,color:#e8f4e8,stroke:#2d8a4f
    style kb fill:#3a2a1a,color:#f4ede8,stroke:#9a6a2f
```

**Key properties:**

| Property | Detail |
|---|---|
| All LLM calls | Route through `tools/llm_client.py` → Anthropic API or Claude CLI |
| Builder batching | Files generated in batches of ≤ 3; earlier files passed as context to later batches |
| Parallelism | Expert + Novice run concurrently via `ThreadPoolExecutor` |
| Resume support | `build_manifest.json` written after initial build; `--resume-from` skips Builder |
| Self-learning | `lessons_learned.md` appended after every run; injected into next Builder prompt |

---

## 2. Full System — Generation + Telemetry

The next phase: every generated repo ships with a telemetry system baked in. Student activity flows to a server; aggregated insights close the loop back into the Builder.

```mermaid
flowchart TB
    subgraph pipeline ["⚙️  Generation Pipeline"]
        direction LR
        CLI2["CLI"] --> Builder2["Builder\n(Planner + Generator)"]
        Builder2 --> Students2["Expert + Novice\nStudent Agents"]
        Students2 -->|"refine if issues"| Builder2
        Students2 -->|"done"| GeneratedRepo
    end

    subgraph inject ["📦  Telemetry Injection  (new — baked into every generated repo)"]
        direction LR
        GeneratedRepo["Challenge Repo"] --> TFiles
        TFiles["telemetry.config.json\n─────────────────────\nstudentId · cohortId\nremoteEndpoint\ntrackTestRuns · trackAI\naiEvaluation settings"]
        TModule["Telemetry Module\n─────────────────────\nTS: src/telemetry/telemetry.ts\n    src/telemetry/vitest-reporter.ts\nPy: src/telemetry/telemetry.py\n    src/telemetry/conftest.py\nJava: TelemetryListener.java"]
        ProgHTML["progress.html\n(student self-view)"]
        Assess["assessment/\npre-assessment.md\npost-assessment.md"]
    end

    subgraph student ["🎓  Student Runtime"]
        direction TB
        RunTests["npm test  /  pytest\n─────────────────────\nTest runner fires\ntelemetry reporter hook"]
        LocalStore[".telemetry/\n─────────────────────\ntest-runs.jsonl\nai-evaluations.jsonl\nassessments.jsonl"]
        LocalView["progress.html\nStudent views own\ntest history locally"]
        AIEval["AI Evaluator\n─────────────────────\nCode quality review\nError pattern analysis\nContextual hints\n(on_test_run trigger)"]

        RunTests --> LocalStore
        RunTests --> AIEval
        AIEval --> LocalStore
        LocalStore --> LocalView
    end

    subgraph server ["🖥️  Telemetry Server  (FastAPI + SQLite)"]
        direction TB
        Ingest["POST /events/{cohort_id}\n─────────────────────\nReceives test run events\nfrom student machines"]
        DB[("SQLite\n─────────\nevents\nstudents\ncohorts")]
        CohortAPI["GET /cohort/{id}\nAggregated JSON"]
        SSE["GET /stream/{cohort_id}\nSSE — real-time push\nto instructor browser"]
        AIInsights["AI Insights Agent\n─────────────────────\nAggregates error patterns\nacross cohort\nGenerates cohort-level\nlearning analysis"]

        Ingest --> DB
        DB --> CohortAPI
        DB --> SSE
        DB --> AIInsights
    end

    subgraph instruct ["👩‍🏫  Instructor Dashboard"]
        direction LR
        Live["Live Feed\n─────────────\nSSE stream\nEvent-by-event\nas students work"]
        Cohort["Cohort View\n─────────────\nAll students\nPass/fail heatmap\nAttempt counts"]
        PerStudent["Per-Student\n─────────────\nTest history\nTime active\nAI evaluations\nAssessment delta"]
    end

    subgraph feedback ["🔄  Feedback Loop"]
        LLMSummary["LLM\n─────────────\nGeneralises cohort\npatterns into reusable\nprinciples"]
        KB2["knowledge_base/\nlessons_learned.md"]
        LLMSummary --> KB2
        KB2 -.->|"injected into\nnext Builder prompt"| Builder2
    end

    inject --> student
    RunTests -->|"POST /events\n(if remoteEndpoint set)"| Ingest
    SSE --> Live
    CohortAPI --> Cohort & PerStudent
    AIInsights --> LLMSummary

    style pipeline fill:#1e3a5f,color:#e8f4f8,stroke:#2d6a9f
    style inject fill:#1e2a4a,color:#ddeeff,stroke:#3a5a8a
    style student fill:#1a3a2a,color:#e8f4e8,stroke:#2d8a4f
    style server fill:#2a1a3a,color:#f0e8ff,stroke:#6a3a9a
    style instruct fill:#2a1a3a,color:#f0e8ff,stroke:#6a3a9a
    style feedback fill:#3a2a1a,color:#f4ede8,stroke:#9a6a2f
```

---

## 3. Demo Flow — End-to-End Sequence

What happens during a live demo, from a single CLI command to an instructor's dashboard updating in real time.

```mermaid
sequenceDiagram
    actor I as 👩‍🏫 Instructor
    actor S as 🎓 Student
    participant CLI as CLI (main.py)
    participant B as Builder Agent
    participant ES as Expert Student
    participant NS as Novice Student
    participant R as Challenge Repo
    participant T as Telemetry Module
    participant FS as FastAPI Server
    participant DB as SQLite
    participant D as Instructor Dashboard

    Note over I,D: ── Phase 1: Generate ──────────────────────────────

    I->>CLI: python main.py --topic "JS Arrays"
    CLI->>B: plan_challenges(topic)
    B-->>CLI: BuildPlan (2 repos, TypeScript ecosystem)
    CLI->>B: generate_repo(spec) × 2
    B-->>CLI: files dict (README + skeleton + tests + telemetry)
    CLI->>ES: evaluate_repo(repo, path)
    CLI->>NS: evaluate_repo(repo, path)
    ES-->>CLI: ExpertFeedback (tests_passed=true)
    NS-->>CLI: NoviceFeedback (clarity=4/5)
    CLI-->>I: ✓ 2 repos generated, tests pass, clarity 4/5

    Note over R: Repo contains telemetry.config.json,<br/>src/telemetry/telemetry.ts,<br/>src/telemetry/vitest-reporter.ts,<br/>progress.html, assessment/

    Note over I,D: ── Phase 2: Student works ──────────────────────────

    I->>S: git clone repo (with remoteEndpoint pre-set)
    S->>R: npm install
    S->>R: npm test  (first attempt — all tests fail)
    R->>T: vitest-reporter.onFinished()
    T->>T: write .telemetry/test-runs.jsonl
    T->>FS: POST /events/{cohort_id}
    FS->>DB: INSERT event (0/8 passed, session abc123)
    FS-->>D: SSE push → "Student joined, 0/8 tests passing"

    S->>R: npm test  (after implementing push/pop)
    R->>T: vitest-reporter.onFinished()
    T->>FS: POST /events/{cohort_id}
    FS->>DB: INSERT event (5/8 passed)
    FS-->>D: SSE push → "Student: 5/8 passing ↑"

    S->>R: npm test  (all done)
    R->>T: vitest-reporter.onFinished()
    T->>FS: POST /events/{cohort_id}
    FS->>DB: INSERT event (8/8 passed)
    FS-->>D: SSE push → "✓ Student completed Stack challenge"

    Note over I,D: ── Phase 3: Instructor view ────────────────────────

    I->>D: GET /cohort/cohort-01
    D->>FS: GET /cohort/cohort-01
    FS->>DB: SELECT * WHERE cohort_id = 'cohort-01'
    DB-->>FS: 4 students, test history, attempt counts
    FS-->>D: JSON cohort summary

    Note over I,D: ── Phase 4: Feedback loop ──────────────────────────

    FS->>DB: aggregate error patterns across cohort
    DB-->>FS: "6/4 students failed 'pop from empty stack'"
    FS->>B: cohort patterns → knowledge_base/lessons_learned.md
    Note over B: Next run: Builder prompted with<br/>"students consistently miss<br/>empty-stack edge cases — emphasise"
```

---

## 4. Telemetry Event Schema

Every test run produces a newline-delimited JSON event appended to `.telemetry/test-runs.jsonl`:

```json
{
  "type": "test_run",
  "timestamp": "2025-03-16T09:15:00.000Z",
  "sessionId": "1710580500000-abc1234",
  "studentId": "alice",
  "cohortId": "cohort-01",
  "challenge": "Stack",
  "testFile": "src/Stack/Stack.test.ts",
  "results": [
    { "name": "should push items onto the stack",      "status": "passed",  "duration": 12 },
    { "name": "should pop in LIFO order",              "status": "passed",  "duration": 8  },
    { "name": "should return undefined on empty pop",  "status": "failed",  "duration": 5,
      "error": "Expected undefined, received null" }
  ],
  "summary": { "total": 8, "passed": 5, "failed": 3, "duration": 47 }
}
```

AI evaluations extend this schema in `.telemetry/ai-evaluations.jsonl`:

```json
{
  "type": "ai_evaluation",
  "timestamp": "2025-03-16T09:15:02.000Z",
  "sessionId": "1710580500000-abc1234",
  "challenge": "Stack",
  "evaluation": {
    "errorPatterns": {
      "identified": ["null-vs-undefined-confusion", "off-by-one-on-empty-check"],
      "rootCause": "Student is checking `this.size === 0` after decrement instead of before"
    },
    "hints": [
      {
        "testName": "should return undefined on empty pop",
        "hint": "Think about when to check if the stack is empty — before or after changing the index?",
        "severity": "gentle"
      }
    ],
    "learningProgress": {
      "conceptsMastered": ["class-structure", "push-logic"],
      "conceptsStruggling": ["boundary-conditions", "index-management"]
    }
  }
}
```

---

## 5. Deployment Topology

```mermaid
flowchart LR
    subgraph local ["Local  (each student's machine)"]
        SR["Challenge Repo\n.telemetry/*.jsonl\nprogress.html"]
    end

    subgraph cloud ["Cloud  (instructor-controlled)"]
        FLY["Railway / Fly.io\n─────────────────\nFastAPI server\nSQLite (or Postgres)\nDocker container"]
        DASH["Instructor Dashboard\nserved by FastAPI"]
    end

    subgraph future ["Future"]
        MULTI["Multi-tenant SaaS\n─────────────────\nCohort management\nAuth / login\nBilling"]
    end

    SR -->|"POST /events\n(background, non-blocking)"| FLY
    FLY --> DASH
    FLY -.->|"v2"| MULTI

    style local fill:#1a3a2a,color:#e8f4e8,stroke:#2d8a4f
    style cloud fill:#2a1a3a,color:#f0e8ff,stroke:#6a3a9a
    style future fill:#3a2a1a,color:#f4ede8,stroke:#9a6a2f,stroke-dasharray:5
```

| Phase | Infrastructure | Effort |
|---|---|---|
| **Now** | Local `.telemetry/` + `progress.html` only | Zero — already generated |
| **Demo** | FastAPI server running on localhost | ~3 hrs |
| **v1** | Single Railway/Fly.io deployment, SQLite | +`Dockerfile` + deploy config |
| **v2** | Postgres, cohort auth, multi-tenant | Full product build |
