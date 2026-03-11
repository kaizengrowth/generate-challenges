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
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
CHALLENGE_TYPES_DIR = KNOWLEDGE_BASE_DIR / "challenge_types"
LESSONS_LEARNED = KNOWLEDGE_BASE_DIR / "lessons_learned.md"
OUTPUT_DIR = ROOT / "output"

# ── LLM Routing ───────────────────────────────────────────────────────────────
# Set USE_CLAUDE_CLI=true in .env to route through your Claude Code subscription.
# Set USE_CLAUDE_CLI=false (default) to use the Anthropic API with ANTHROPIC_API_KEY.
USE_CLAUDE_CLI: bool = os.getenv("USE_CLAUDE_CLI", "false").lower() == "true"

# Models (used in API mode; CLI mode uses whatever model claude defaults to)
BUILDER_MODEL = "claude-sonnet-4-6"
EXPERT_STUDENT_MODEL = "claude-sonnet-4-6"
NOVICE_STUDENT_MODEL = "claude-haiku-4-5-20251001"
RECOMMENDER_MODEL = "claude-haiku-4-5-20251001"
SUMMARIZE_CHANGES_MODEL = "claude-haiku-4-5-20251001"

# Refinement loop
MAX_ITERATIONS = 3

# Token limits (API mode only)
BUILDER_MAX_TOKENS = 16000
STUDENT_MAX_TOKENS = 8000
RECOMMENDER_MAX_TOKENS = 2000
