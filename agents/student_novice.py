"""
Novice Student Agent — evaluates challenge clarity and pedagogy.

Reads all challenge files (including test source) and evaluates from a confused
bootcamp student's perspective: README clarity, test name quality, difficulty, missing context.
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
    test_name_quality: list[str] = field(default_factory=list)

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


def evaluate_repo(
    repo: ChallengeRepo,
    repo_dir: Path,
) -> NoviceFeedback:
    """
    Run novice student evaluation on a challenge repo.

    Args:
        repo: the ChallengeRepo metadata
        repo_dir: path to the repo on disk
    """
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
        agent="Novice Student",
    )
    wb_data = parse_json_from_response(wb_raw, context="Novice Student")

    return NoviceFeedback(
        clarity_score=wb_data.get("clarity_score", 3),
        difficulty_assessment=wb_data.get("difficulty_assessment", "appropriate"),
        confusion_points=wb_data.get("confusion_points", []),
        missing_context=wb_data.get("missing_context", []),
        test_name_quality=wb_data.get("test_name_quality", []),
    )
