import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root
ROOT = Path(__file__).parent

# Paths
REFERENCES_DIR = ROOT / "references"
GENERATION_PATTERNS = REFERENCES_DIR / "generation-patterns.md"
PROJECT_TEMPLATES = REFERENCES_DIR / "project-templates.md"
UI_STYLING = REFERENCES_DIR / "ui-styling.md"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
CHALLENGE_TYPES_DIR = KNOWLEDGE_BASE_DIR / "challenge_types"
LESSONS_LEARNED = KNOWLEDGE_BASE_DIR / "lessons_learned.md"
OUTPUT_DIR = ROOT / "output"

# ── LLM Routing ───────────────────────────────────────────────────────────────
# Set USE_CLAUDE_CLI=true in .env to route through your Claude Code subscription.
# Set USE_CLAUDE_CLI=false (default) to use the Anthropic API with ANTHROPIC_API_KEY.
USE_CLAUDE_CLI: bool = os.getenv("USE_CLAUDE_CLI", "false").lower() == "true"

# Models (used in API mode; CLI mode uses whatever model claude defaults to)
PLANNER_MODEL = "claude-haiku-4-5-20251001"
BUILDER_MODEL = "claude-sonnet-4-6"
EXPERT_STUDENT_MODEL = "claude-sonnet-4-6"
NOVICE_STUDENT_MODEL = "claude-haiku-4-5-20251001"
RECOMMENDER_MODEL = "claude-haiku-4-5-20251001"
SUMMARIZE_CHANGES_MODEL = "claude-haiku-4-5-20251001"

# Refinement loop
MAX_ITERATIONS = 2

# Token limits (API mode only)
PLANNER_MAX_TOKENS = 2000
BUILDER_MAX_TOKENS = 16000
STUDENT_MAX_TOKENS = 8000
RECOMMENDER_MAX_TOKENS = 2000

# Max creative files per LLM call (batches generation to avoid timeouts and truncation).
# Applies to both CLI and API mode:
#   CLI — each call is a subprocess with a 600s wall; large repos hit it without batching
#   API — each call is bounded by BUILDER_MAX_TOKENS; batching prevents truncated JSON
# Each file averages ~100-200 lines; 3 files ≈ 400-600 lines ≈ 1,500-2,500 output tokens
# Lower values = more calls but each finishes faster; minimum useful value is 1
BUILDER_MAX_FILES_PER_BATCH = 3

# CLI mode timeout (seconds) — builder can generate large responses
CLI_TIMEOUT = 600

# ── Telemetry ─────────────────────────────────────────────────────────────────
# Set TELEMETRY_ENABLED=false to skip telemetry injection in generated repos.
# Set TELEMETRY_ENDPOINT to pre-configure a remote server in every generated repo.
#   e.g. TELEMETRY_ENDPOINT=http://localhost:8000/events
# Leave unset (or empty) for local-only mode (events write to .telemetry/ only).
TELEMETRY_ENABLED: bool = os.getenv("TELEMETRY_ENABLED", "true").lower() == "true"
TELEMETRY_ENDPOINT: str | None = os.getenv("TELEMETRY_ENDPOINT") or None
