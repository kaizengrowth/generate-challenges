# Challenge Generation Platform

A multi-agent Python application that generates testable coding challenges for bootcamp students. Given a topic, it recommends challenges, builds complete self-contained git repos (README + skeleton files + tests), runs two simulated student agents to validate quality, and iteratively refines the output.

---

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

Configure `.env` (the file is gitignored — never commit it):

```bash
# Option A — use your Claude Max/Pro subscription (no API key needed)
USE_CLAUDE_CLI=true

# Option B — use the Anthropic API directly
USE_CLAUDE_CLI=false
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Generate challenges for a topic

Runs the Recommender, displays a table of suggested challenges, lets you pick which ones to build, then runs the full pipeline.

```bash
python main.py --topic "React state management"
python main.py --topic "JavaScript closures"
python main.py --topic "GitHub Actions CI/CD"
```

### Generate specific challenges directly (skip Recommender)

```bash
python main.py --challenge "Build a click counter in React"
python main.py --challenge "Build a click counter" --challenge "Build a toggle switch"

# With a topic label (used for the output folder name)
python main.py --topic "React" --challenge "Build a click counter" --challenge "Build a toggle"
```

### Resume an interrupted run (skip the Builder)

If the pipeline crashed during student evaluation, resume from where it left off — the Builder is skipped and the already-generated repos are reused:

```bash
python main.py --resume-from output/react-state-management
```

### Common flags

```bash
# Skip student validation entirely — just generate the challenge files
python main.py --topic "Python async" --no-refine

# Skip the novice student pass (only Expert runs) — faster
python main.py --topic "Python async" --skip-novice

# Override the number of refinement iterations (default: 3)
python main.py --topic "Python async" --max-iterations 2

# Pass instructor notes directly to the Builder
python main.py --topic "Python async" --notes "Focus on asyncio.gather and error handling"

# Write output to a custom directory
python main.py --topic "Python async" --output-dir ~/challenges/python-async
```

### Combining flags

```bash
# Generate specific challenges, skip novice review, allow up to 2 refinement passes
python main.py \
  --challenge "Fix the stale closure bug" \
  --challenge "Implement optimistic UI with rollback" \
  --topic "React hooks" \
  --skip-novice \
  --max-iterations 2

# Generate fast — no refinement, no student validation
python main.py --topic "Redux patterns" --no-refine

# Resume a failed run, but this time skip the novice pass
python main.py --resume-from output/react-state-management --skip-novice
```

---

## Output Structure

```
output/
└── react-state-management/           # topic slug
    ├── build_manifest.json           # resume checkpoint (repo metadata)
    ├── iteration_log.json            # per-iteration feedback summary
    ├── react-hooks-patterns/         # self-contained git repo (student receives this)
    │   ├── .git/
    │   ├── README.md
    │   ├── package.json
    │   ├── src/                      # skeleton files (empty / broken on purpose)
    │   └── tests/
    └── reference_solutions/
        └── react-hooks-patterns/     # expert student's working solution
```

Each repo can be handed directly to a student:

```bash
cd output/react-state-management/react-hooks-patterns
npm install
npm test    # tests should fail until the student implements the solution
```

---

## Development

### Run the test suite

```bash
# Run all tests (zero LLM tokens used — everything is mocked)
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_orchestrator.py -v

# Run a specific test class or test
python -m pytest tests/test_orchestrator.py::TestResumePipeline -v
python -m pytest tests/test_builder.py::TestBuildChallenges::test_returns_build_result -v
```

### Project layout

```
main.py                      CLI entry point (typer + rich)
config.py                    All paths, model names, env var loading
agents/
  recommender.py             Topic → candidate challenges (instructor selects)
  builder.py                 Generates complete challenge repos from descriptions
  student_expert.py          Validates challenges technically; writes reference solution
  student_novice.py          Reviews challenges as a confused bootcamp student
  orchestrator.py            Runs the full pipeline + refinement loop
tools/
  llm_client.py              Routes LLM calls to Anthropic API or Claude CLI
  file_tools.py              Read/write files, format for prompts
  repo_tools.py              git init + initial commit
  subprocess_tools.py        Run install/test commands, capture output
knowledge_base/
  challenge_types/           Builder writes here when it figures out a new challenge type
  lessons_learned.md         Cross-cutting insights appended after each run
skill/                       Original standalone Claude Code skill (still usable)
tests/                       Full unit test suite (130 tests, zero LLM tokens)
```
