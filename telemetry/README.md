# Telemetry — Student Learning Dashboard

This folder contains everything for the student telemetry system: the server that ingests learning events, the instructor dashboard, and the architecture documentation.

This work is kept separate from the core challenge generation pipeline in the root of this repo.

---

## What Goes Here

```
telemetry/
├── ARCHITECTURE.md        # System design, diagrams, data schema, deployment plan
├── README.md              # This file
├── server/                # FastAPI ingest server + SQLite storage  (to build)
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   │   ├── events.py      # POST /events/{cohort_id}
│   │   ├── cohort.py      # GET  /cohort/{id}
│   │   └── stream.py      # GET  /stream/{cohort_id}  (SSE)
│   ├── db.py
│   └── requirements.txt
└── dashboard/             # Instructor dashboard UI  (to build)
    └── index.html
```

## Related: Skill Layer

The Cursor agent skill that injects telemetry files into generated challenge repos lives in `skill/` at the repo root (see `skill/SKILL.md` and `skill/references/telemetry-system.md`). That's the *generation* side; this folder is the *collection and display* side.

---

## Quick Links

- [Architecture diagrams and data schema](./ARCHITECTURE.md)
- [Generation pipeline (root repo)](../README.md)
