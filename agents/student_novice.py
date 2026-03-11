"""
Novice Student Agent — evaluates challenge clarity and pedagogy.

Runs two passes:
  White-box: can see test source — evaluates test names, descriptions, whether tests reveal too much
  Black-box: can only see test runner output — evaluates if a student would know what to do next
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import config
from agents.builder import ChallengeRepo
from tools.file_tools import read_repo_files, format_files_for_prompt
from tools.llm_client import call_llm, parse_json_from_response


@dataclass
class NoviceFeedback:
    clarity_score: int  # 1-5
    difficulty_assessment: str  # "too easy" | "appropriate" | "too hard"
    confusion_points: list[str] = field(default_factory=list)
    missing_context: list[str] = field(default_factory=list)
    test_name_quality: list[str] = field(default_factory=list)  # white-box
    error_message_quality: list[str] = field(default_factory=list)  # black-box

    @property
    def has_issues(self) -> bool:
        return self.clarity_score < 4 or bool(self.confusion_points) or bool(self.missing_context)

    def to_feedback_text(self) -> str:
        parts = [
            f"### Novice Student Evaluation",
            f"Clarity score: {self.clarity_score}/5",
            f"Difficulty: {self.difficulty_assessment}",
        ]
        if self.confusion_points:
            parts.append("### Confusion Points\n" + "\n".join(f"- {p}" for p in self.confusion_points))
        if self.missing_context:
            parts.append("### Missing Context\n" + "\n".join(f"- {m}" for m in self.missing_context))
        if self.test_name_quality:
            parts.append("### Test Name/Description Quality\n" + "\n".join(f"- {t}" for t in self.test_name_quality))
        if self.error_message_quality:
            parts.append("### Error Message Feedback\n" + "\n".join(f"- {e}" for e in self.error_message_quality))
        return "\n\n".join(parts)


WHITEBOX_SYSTEM_PROMPT = """You are a student midway through a coding bootcamp. You are eager to learn
but sometimes get confused by jargon, ambiguous instructions, or challenges that assume too much prior knowledge.

You can see ALL files including the test source code.

Evaluate this challenge from a student's perspective:
- Is the README clear about what you need to implement?
- Do the test names and descriptions help you understand what's expected?
- Do the tests reveal too much (spoiling the solution) or too little?
- Is the difficulty appropriate for a bootcamp student who just learned this topic?
- What's missing that would help you get started?

Output ONLY a valid JSON object:
{
  "clarity_score": 4,
  "difficulty_assessment": "appropriate",
  "confusion_points": ["The term 'memoization' is used without explanation", "Unclear if I should modify the existing class or create a new one"],
  "missing_context": ["An example of what the final output should look like would help", "No starter code makes it hard to know where to begin"],
  "test_name_quality": ["Test 'should work correctly' is too vague — what does 'correctly' mean?", "Test names clearly describe expected behavior"]
}

Rules:
- clarity_score: 1 (very confusing) to 5 (crystal clear)
- difficulty_assessment: "too easy", "appropriate", or "too hard"
- If a category has no issues, use an empty array []
- Be specific — quote exact words or phrases that confused you
- Output ONLY the JSON, no markdown fences
"""

BLACKBOX_SYSTEM_PROMPT = """You are a student midway through a coding bootcamp. You have just run the tests
on a challenge for the first time. You can ONLY see the test runner output — not the test source code.

Evaluate the test output as a learning experience:
- Can you tell from the failure messages what you need to implement?
- Are the error messages helpful or cryptic?
- Would you know what to do next?

Output ONLY a valid JSON object:
{
  "error_message_quality": ["observation 1", "observation 2"]
}

Rules:
- Focus on whether failure messages guide students toward the solution
- Be specific — quote actual error text when commenting on it
- If messages are clear, say so (e.g., "Error 'expected undefined to be a function' clearly tells me I need to define the method")
- Output ONLY the JSON, no markdown fences
"""


def evaluate_repo(
    repo: ChallengeRepo,
    repo_dir: Path,
    test_output: str,
) -> NoviceFeedback:
    """
    Run novice student evaluation on a challenge repo.

    Args:
        repo: the ChallengeRepo metadata
        repo_dir: path to the repo on disk
        test_output: raw test runner output (from expert student's test run)
    """
    # Exclude test files for white-box pass — wait, novice CAN see tests in white-box
    all_files = read_repo_files(repo_dir)

    # ── White-box pass ──────────────────────────────────────────────────────
    wb_prompt = (
        f"Challenge topic: {repo.description}\n\n"
        f"Challenges covered: {', '.join(repo.challenges)}\n\n"
        f"## All Challenge Files\n\n{format_files_for_prompt(all_files)}"
    )

    wb_raw = call_llm(
        system=WHITEBOX_SYSTEM_PROMPT,
        user=wb_prompt,
        model=config.NOVICE_STUDENT_MODEL,
        max_tokens=config.STUDENT_MAX_TOKENS,
    )
    wb_data = parse_json_from_response(wb_raw, context="Novice Student (white-box)")

    # ── Black-box pass ──────────────────────────────────────────────────────
    bb_prompt = (
        f"Challenge topic: {repo.description}\n\n"
        f"Test runner output (first run with skeleton code, before I've implemented anything):\n"
        f"```\n{test_output}\n```"
    )

    bb_raw = call_llm(
        system=BLACKBOX_SYSTEM_PROMPT,
        user=bb_prompt,
        model=config.NOVICE_STUDENT_MODEL,
        max_tokens=1000,
    )
    bb_data = parse_json_from_response(bb_raw, context="Novice Student (black-box)")

    return NoviceFeedback(
        clarity_score=wb_data.get("clarity_score", 3),
        difficulty_assessment=wb_data.get("difficulty_assessment", "appropriate"),
        confusion_points=wb_data.get("confusion_points", []),
        missing_context=wb_data.get("missing_context", []),
        test_name_quality=wb_data.get("test_name_quality", []),
        error_message_quality=bb_data.get("error_message_quality", []),
    )
