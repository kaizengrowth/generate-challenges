"""
Expert Student Agent — attempts to solve challenges, runs tests, evaluates quality.

Reads all challenge files, writes a reference solution, and runs the tests to verify it passes.
"""

import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import config
from agents.builder import ChallengeRepo
from tools.file_tools import read_repo_files, write_repo_files, format_files_for_prompt
from tools.llm_client import call_llm, parse_json_from_response
from tools.subprocess_tools import run_tests, TestResult


@dataclass
class ExpertFeedback:
    solved: bool
    tests_passed: bool
    test_output: str  # raw output from test runner

    test_quality_issues: list[str] = field(default_factory=list)
    infrastructure_issues: list[str] = field(default_factory=list)
    technical_issues: list[str] = field(default_factory=list)

    # Reference solution files (relative_path -> content)
    solution_files: dict[str, str] = field(default_factory=dict)

    @property
    def has_issues(self) -> bool:
        return bool(
            self.test_quality_issues
            or self.infrastructure_issues
            or self.technical_issues
            or not self.tests_passed
        )

    def to_feedback_text(self) -> str:
        parts = []
        if not self.tests_passed:
            lines = self.test_output.splitlines()
            if len(lines) > 100:
                output = "\n".join(lines[:100]) + f"\n... ({len(lines) - 100} more lines truncated)"
            else:
                output = self.test_output
            parts.append(f"### Tests did not pass\nTest output:\n```\n{output}\n```")
        if self.infrastructure_issues:
            parts.append("### Infrastructure Issues\n" + "\n".join(f"- {i}" for i in self.infrastructure_issues))
        if self.test_quality_issues:
            parts.append("### Test Quality Issues\n" + "\n".join(f"- {i}" for i in self.test_quality_issues))
        if self.technical_issues:
            parts.append("### Technical Issues\n" + "\n".join(f"- {i}" for i in self.technical_issues))
        return "\n\n".join(parts)


WHITEBOX_SYSTEM_PROMPT = """You are an expert software engineer reviewing a coding challenge for a bootcamp.
You have access to all challenge files including the test source code.

Your job:
1. Review the test files for quality issues (wrong assertions, tests that are impossible to pass, tests that don't actually test what they claim, missing edge cases that should be tested)
2. Review the infrastructure (build config, skeleton files) for correctness
3. Write a complete, correct solution to the challenge
4. Identify any technical issues that would prevent students from completing the challenge

Output ONLY a valid JSON object:
{
  "infrastructure_issues": ["issue 1", "issue 2"],
  "test_quality_issues": ["issue 1", "issue 2"],
  "technical_issues": ["issue 1", "issue 2"],
  "solution_files": {
    "src/ClickCounter.tsx": "...complete solution...",
    "src/utils.py": "...complete solution..."
  }
}

Rules:
- Only include keys for files that NEED to be created or modified for the solution
- Do NOT modify test files, config files, or README in your solution_files
- solution_files should contain only implementation files
- If there are no issues for a category, use an empty array []
- All file contents must be complete and valid
- Output ONLY the JSON, no markdown fences
"""


def evaluate_repo(repo: ChallengeRepo, repo_dir: Path) -> ExpertFeedback:
    """
    Run expert student evaluation on a challenge repo.

    1. Read all files, evaluate test quality, write a reference solution
    2. Run the solution's tests and verify they pass
    """
    all_files = read_repo_files(repo_dir)

    # ── White-box pass ──────────────────────────────────────────────────────
    whitebox_prompt = (
        f"Challenge: {repo.description}\n\n"
        f"Challenges covered: {', '.join(repo.challenges)}\n\n"
        f"## All Challenge Files\n\n{format_files_for_prompt(all_files)}"
    )

    wb_raw = call_llm(
        system=WHITEBOX_SYSTEM_PROMPT,
        user=whitebox_prompt,
        model=config.EXPERT_STUDENT_MODEL,
        max_tokens=config.STUDENT_MAX_TOKENS,
        agent="Expert Student",
    )
    wb_data = parse_json_from_response(wb_raw, context="Expert Student (white-box)")

    solution_files = wb_data.get("solution_files", {})
    infrastructure_issues = wb_data.get("infrastructure_issues", [])
    test_quality_issues = wb_data.get("test_quality_issues", [])
    technical_issues = wb_data.get("technical_issues", [])

    # ── Run the solution ────────────────────────────────────────────────────
    test_result = _run_solution(repo, repo_dir, solution_files)

    return ExpertFeedback(
        solved=test_result.passed,
        tests_passed=test_result.passed,
        test_output=test_result.combined,
        test_quality_issues=test_quality_issues,
        infrastructure_issues=infrastructure_issues,
        technical_issues=technical_issues,
        solution_files=solution_files,
    )


def _run_solution(repo: ChallengeRepo, repo_dir: Path, solution_files: dict[str, str]) -> TestResult:
    """Write solution files into a temp copy of the repo and run tests."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp) / repo.name
        # Copy original repo
        shutil.copytree(repo_dir, tmp_dir, ignore=shutil.ignore_patterns(".git"))
        # Overlay solution files
        write_repo_files(tmp_dir, solution_files)
        # Run tests
        return run_tests(tmp_dir, repo.install_command, repo.test_command)


def save_reference_solution(
    solution_files: dict[str, str],
    reference_dir: Path,
    repo_name: str,
) -> None:
    """Save the expert's reference solution alongside the challenge repo."""
    dest = reference_dir / repo_name
    dest.mkdir(parents=True, exist_ok=True)
    for rel_path, content in solution_files.items():
        file_path = dest / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
