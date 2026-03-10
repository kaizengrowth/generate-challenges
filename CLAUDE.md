# Challenge Generation Platform

A Python agentic application that generates testable coding challenges for bootcamp students. Given a topic, it recommends challenges, builds complete self-contained git repos (README + skeleton files + tests), runs two simulated student agents to validate quality, and iteratively refines the output.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Configure `.env` (copy from `.env.example` if needed — it is gitignored):
```bash
USE_CLAUDE_CLI=true           # use Claude Code subscription (no API key needed)
# or
USE_CLAUDE_CLI=false
ANTHROPIC_API_KEY=sk-ant-...  # required when USE_CLAUDE_CLI=false
```

## Running the App

```bash
# Topic mode — runs recommender, instructor selects interactively
python main.py --topic "React state management"

# Direct mode — skip recommender, build specific challenges
python main.py --challenge "Build a click counter" --challenge "Build a toggle"

# Resume after a crash — skip the Builder, reuse repos already on disk
python main.py --resume-from output/react-state-management

# Common flags
--no-refine        # generate only, skip student validation (fastest)
--skip-novice      # skip novice student pass, only run expert (faster)
--max-iterations 2 # override refinement loop limit (default: 3)
--notes "..."      # pass instructor guidance directly to the builder
--output-dir ...   # override default output location
--resume-from DIR  # resume from an existing output directory
```

Output lands in `output/{topic-slug}/` — each challenge cluster is its own independent git repo, fully runnable with just `install + test`.

## Architecture

```
main.py                  CLI entry point (typer + rich)
config.py                All paths, model names, env var loading
agents/
  recommender.py         Topic → 5-10 candidate challenges (instructor selects)
  builder.py             Generates complete challenge repos from descriptions
  student_expert.py      Validates challenges technically; writes reference solution
  student_novice.py      Reviews challenges as a confused bootcamp student
  orchestrator.py        Runs the full pipeline + refinement loop
tools/
  llm_client.py          Routes LLM calls to API or Claude CLI
  file_tools.py          Read/write files, format for prompts
  repo_tools.py          git init + initial commit
  subprocess_tools.py    Run install/test commands, capture output
skill/
  SKILL.md               Original Claude Code skill (still usable standalone)
  references/            Reference docs injected into every builder prompt
    generation-patterns.md
    project-templates.md
knowledge_base/
  challenge_types/       Builder writes here when it figures out a new challenge type
  lessons_learned.md     Cross-cutting insights appended after each run
output/                  Generated challenge repos (gitignored)
```

## Pipeline Flow

```
--topic → Recommender → instructor selects → Builder → Expert Student → Novice Student
                                                  ↑                           |
                                                  └── feedback (if issues) ───┘
                                                  (up to MAX_ITERATIONS times)
```

1. **Recommender** — asks Claude for 5-10 challenge ideas; instructor picks from a rich table in the terminal
2. **Builder** — generates a full JSON blob of file paths + contents; these get written to disk and `git init`-ed
3. **Expert Student** — white-box pass (reads test source, evaluates quality, writes solution) then runs real tests via subprocess; black-box pass (evaluates test runner output as a student would see it)
4. **Novice Student** — white-box pass (reviews for clarity, test name quality) then black-box pass (would a student understand these error messages?)
5. **Refinement** — if either student found issues and iterations remain, structured feedback is sent back to Builder; loop repeats
6. **Output** — final challenge repo, reference solution, `iteration_log.json`

## LLM Routing (`tools/llm_client.py`)

All LLM calls go through `call_llm(system, user, model, max_tokens)`. It checks `config.USE_CLAUDE_CLI`:
- **API mode** (`False`): uses `anthropic.Anthropic().messages.create(...)` with `ANTHROPIC_API_KEY`
- **CLI mode** (`True`): shells out to `claude --print --model <model> <prompt>`. The system prompt is prepended as `<system>...</system>` since the CLI doesn't expose a separate system flag in print mode.

When modifying agent logic, always use `call_llm` — never import `anthropic` directly in agent files.

## Builder Output Format

The Builder is prompted to return a single JSON object. All agents parse JSON from LLM responses. The pattern for handling responses is consistent across all agents:

```python
raw = call_llm(system=..., user=..., model=..., max_tokens=...)
if raw.startswith("```"):
    raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
data = json.loads(raw)
```

If a builder response fails to parse, the issue is almost always the model wrapping JSON in markdown fences despite being told not to — the strip logic above handles it.

## Knowledge Base (Self-Learning)

The Builder writes to `knowledge_base/challenge_types/{slug}.md` whenever it figures out how to handle a challenge type it hasn't seen before. On subsequent runs, these files are injected into the builder's context. This means:
- First run of "GitHub Actions CI/CD" challenges → Builder reasons from scratch, saves its approach
- Second run → Builder starts from saved approach (faster, more consistent)

`knowledge_base/lessons_learned.md` is appended after every run with issues that needed refinement. Both files are gitignored (they live only on your machine and grow over time).

## Adding a New Agent

1. Create `agents/my_agent.py`
2. Import `call_llm` from `tools/llm_client`, `config` for model names
3. Define a `@dataclass` for the return type
4. Write a `SYSTEM_PROMPT` constant
5. Write a function that calls `call_llm`, strips fences, parses JSON, returns the dataclass
6. Wire it into `agents/orchestrator.py`

## Key Conventions

- **Agents return dataclasses**, not raw dicts — makes the orchestrator readable
- **`has_issues` property** on feedback dataclasses — the orchestrator uses this to decide whether to refine
- **`to_feedback_text()` method** on feedback dataclasses — formats issues for the Builder's revision prompt
- **Skeleton files never contain solutions** — tests start red, turn green as students implement
- **Each challenge cluster is one git repo** — the Builder decides clustering; repos land in `output/{topic}/`
- **Reference solutions are stored outside the student repo** — in `output/{topic}/reference_solutions/`
- Python 3.12+ — uses `dict[str, str]` and `list[str]` type hints directly (no `from __future__ import annotations` needed)

## Reference Docs

`skill/references/generation-patterns.md` and `skill/references/project-templates.md` are injected verbatim into every Builder prompt. They contain:
- Skeleton and test examples for every supported language (TS/JS, React, Python, Java, Angular, C++, COBOL, Vue)
- Build config templates (package.json, pom.xml, requirements.txt, CMakeLists.txt, etc.)
- Decision guide: what signals in a README map to what skeleton/test style

If you add a new language or challenge pattern, add it to these files — the Builder will pick it up automatically on the next run.
