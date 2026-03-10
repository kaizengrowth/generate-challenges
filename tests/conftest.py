"""
Shared fixtures and factory helpers for all tests.

Key design decisions:
- `isolated_config` (autouse) redirects all config file paths to tmp_path so
  tests never read/write the real knowledge_base or output directories.
- Factory helpers (make_challenge_repo, make_expert_feedback, make_novice_feedback)
  produce valid dataclass instances with sensible defaults.
- Canonical JSON strings (BUILDER_RESPONSE etc.) are the mock LLM responses
  used across agent tests.
"""

import json
import pytest

import config
from agents.builder import ChallengeRepo, BuildResult
from agents.student_expert import ExpertFeedback
from agents.student_novice import NoviceFeedback

# ── Canonical mock LLM response strings ──────────────────────────────────────

BUILDER_RESPONSE = json.dumps({
    "repos": [
        {
            "name": "click-counter",
            "description": "A React click counter challenge",
            "challenges": ["Click Counter"],
            "install_command": "npm install",
            "test_command": "npm test",
            "files": {
                "README.md": "# Click Counter\nBuild a click counter.",
                "package.json": '{"name":"click-counter","scripts":{"test":"vitest"}}',
                "src/ClickCounter.tsx": "export default function ClickCounter() { return null; }",
                ".gitignore": "node_modules/",
            },
        }
    ],
    "clustering_rationale": "Single challenge, single repo",
    "challenge_type_notes": "",
})

BUILDER_RESPONSE_WITH_NOTES = json.dumps({
    "repos": [
        {
            "name": "debug-challenge",
            "description": "A debugging challenge",
            "challenges": ["Fix the Bug"],
            "install_command": "npm install",
            "test_command": "npm test",
            "files": {"README.md": "# Debug\nFind the bug."},
        }
    ],
    "clustering_rationale": "Single repo",
    "challenge_type_notes": "For debugging challenges, provide broken code with logic errors.",
})

EXPERT_WHITEBOX_RESPONSE = json.dumps({
    "infrastructure_issues": [],
    "test_quality_issues": [],
    "technical_issues": [],
    "solution_files": {
        "src/ClickCounter.tsx": "export default function ClickCounter() { return <button>0</button>; }",
    },
})

EXPERT_WHITEBOX_WITH_ISSUES = json.dumps({
    "infrastructure_issues": ["Missing tsconfig.json"],
    "test_quality_issues": ["Test assertions are too broad"],
    "technical_issues": ["Import path is incorrect"],
    "solution_files": {"src/ClickCounter.tsx": "// solution"},
})

EXPERT_BLACKBOX_RESPONSE = json.dumps({
    "error_message_quality": ["Messages clearly indicate what needs to be implemented"],
})

NOVICE_WHITEBOX_RESPONSE = json.dumps({
    "clarity_score": 4,
    "difficulty_assessment": "appropriate",
    "confusion_points": [],
    "missing_context": [],
    "test_name_quality": ["Test names are descriptive"],
})

NOVICE_WHITEBOX_WITH_ISSUES = json.dumps({
    "clarity_score": 2,
    "difficulty_assessment": "too hard",
    "confusion_points": ["The term 'memoization' is not explained"],
    "missing_context": ["No example output provided"],
    "test_name_quality": [],
})

NOVICE_BLACKBOX_RESPONSE = json.dumps({
    "error_message_quality": ["Error messages are actionable"],
})

RECOMMENDER_RESPONSE = json.dumps({
    "candidates": [
        {
            "title": "Click Counter",
            "description": "Build a button that increments a displayed count",
            "learning_objective": "Practice useState hook",
            "difficulty": "beginner",
            "challenge_type": "implementation",
        },
        {
            "title": "Toggle Visibility",
            "description": "Show/hide content with a button",
            "learning_objective": "Practice conditional rendering",
            "difficulty": "beginner",
            "challenge_type": "implementation",
        },
        {
            "title": "Live Input Preview",
            "description": "Display text as the user types",
            "learning_objective": "Practice onChange handlers",
            "difficulty": "intermediate",
            "challenge_type": "implementation",
        },
    ]
})


# ── Config isolation (autouse — applies to every test) ───────────────────────

@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect all config file paths to tmp_path to avoid touching real files."""
    kb = tmp_path / "knowledge_base"
    kb.mkdir()
    ct = kb / "challenge_types"
    ct.mkdir()
    ll = kb / "lessons_learned.md"
    ll.write_text("# Lessons Learned\n")

    monkeypatch.setattr(config, "KNOWLEDGE_BASE_DIR", kb)
    monkeypatch.setattr(config, "CHALLENGE_TYPES_DIR", ct)
    monkeypatch.setattr(config, "LESSONS_LEARNED", ll)
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)


# ── Dataclass factory helpers ─────────────────────────────────────────────────

def make_challenge_repo(**kwargs) -> ChallengeRepo:
    defaults = dict(
        name="click-counter",
        description="A React click counter challenge",
        challenges=["Click Counter"],
        install_command="npm install",
        test_command="npm test",
        files={"README.md": "# Click Counter"},
    )
    defaults.update(kwargs)
    return ChallengeRepo(**defaults)


def make_build_result(**repo_kwargs) -> BuildResult:
    return BuildResult(repos=[make_challenge_repo(**repo_kwargs)])


def make_expert_feedback(tests_passed: bool = True, **kwargs) -> ExpertFeedback:
    defaults = dict(
        solved=tests_passed,
        tests_passed=tests_passed,
        test_output="All tests passed" if tests_passed else "2 tests failed",
        technical_issues=[],
        test_quality_issues=[],
        infrastructure_issues=[],
        error_message_quality=[],
        solution_files={"src/ClickCounter.tsx": "// solution"},
    )
    defaults.update(kwargs)
    return ExpertFeedback(**defaults)


def make_novice_feedback(clarity_score: int = 5, **kwargs) -> NoviceFeedback:
    defaults = dict(
        clarity_score=clarity_score,
        difficulty_assessment="appropriate",
        confusion_points=[],
        missing_context=[],
        test_name_quality=[],
        error_message_quality=[],
    )
    defaults.update(kwargs)
    return NoviceFeedback(**defaults)
