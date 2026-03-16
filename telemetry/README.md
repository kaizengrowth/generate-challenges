# Telemetry — Student Learning Dashboard

This folder contains everything for the student telemetry system: the server that ingests learning events, the instructor dashboard, and the architecture documentation.

This work is kept separate from the core challenge generation pipeline in the root of this repo.

---

## What Goes Here

```
telemetry/
├── ARCHITECTURE.md        # System design, diagrams, data schema, deployment plan
├── README.md              # This file
├── server/                # FastAPI ingest server + SQLite storage
│   ├── main.py            # POST /events, GET /cohort/{id}, GET /stream/{id} (SSE)
│   ├── db.py              # SQLite schema + query helpers
│   ├── seed.py            # Pre-populates 3 realistic demo students
│   ├── instructor.html    # Instructor dashboard (student grid, heatmap, live feed)
│   └── requirements.txt
└── demo-challenge/        # Manually scaffolded Stack challenge with telemetry
    ├── src/Stack.ts       # Empty skeleton — implement to make tests pass
    ├── src/telemetry/     # Telemetry module (auto-injected by Builder in all repos)
    ├── tests/Stack.test.ts
    ├── telemetry.config.json
    └── progress.html      # Student self-view dashboard
```

## Related: Skill Layer

The Cursor agent skill that injects telemetry files into generated challenge repos lives in `skill/` at the repo root (see `skill/SKILL.md` and `skill/references/telemetry-system.md`). That's the *generation* side; this folder is the *collection and display* side.

---

## Quick Links

- [Architecture diagrams and data schema](./ARCHITECTURE.md)
- [Generation pipeline (root repo)](../README.md)
