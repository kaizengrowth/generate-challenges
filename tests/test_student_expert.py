"""Tests for agents/student_expert.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.builder import ChallengeRepo
from agents.student_expert import (
    ExpertFeedback,
    evaluate_repo,
    save_reference_solution,
)
from tests.conftest import (
    EXPERT_WHITEBOX_RESPONSE,
    EXPERT_WHITEBOX_WITH_ISSUES,
    make_challenge_repo,
)
from tools.subprocess_tools import TestResult


def _make_test_result(passed: bool = True) -> TestResult:
    return TestResult(
        exit_code=0 if passed else 1,
        stdout="All passed" if passed else "",
        stderr="" if passed else "2 failed",
        combined="All passed" if passed else "2 failed",
    )


class TestExpertFeedbackDataclass:
    def test_has_issues_false_when_clean(self):
        fb = ExpertFeedback(
            solved=True, tests_passed=True, test_output="ok",
            technical_issues=[], test_quality_issues=[], infrastructure_issues=[],
        )
        assert fb.has_issues is False

    def test_has_issues_true_when_tests_fail(self):
        fb = ExpertFeedback(solved=False, tests_passed=False, test_output="fail")
        assert fb.has_issues is True

    def test_has_issues_true_when_technical_issues(self):
        fb = ExpertFeedback(
            solved=True, tests_passed=True, test_output="ok",
            technical_issues=["bad import"],
        )
        assert fb.has_issues is True

    def test_has_issues_true_when_test_quality_issues(self):
        fb = ExpertFeedback(
            solved=True, tests_passed=True, test_output="ok",
            test_quality_issues=["test asserts wrong thing"],
        )
        assert fb.has_issues is True

    def test_has_issues_true_when_infrastructure_issues(self):
        fb = ExpertFeedback(
            solved=True, tests_passed=True, test_output="ok",
            infrastructure_issues=["missing config"],
        )
        assert fb.has_issues is True

    def test_to_feedback_text_includes_test_failure(self):
        fb = ExpertFeedback(solved=False, tests_passed=False, test_output="3 failed")
        text = fb.to_feedback_text()
        assert "Tests did not pass" in text
        assert "3 failed" in text

    def test_to_feedback_text_includes_all_issue_types(self):
        fb = ExpertFeedback(
            solved=False, tests_passed=False, test_output="fail",
            infrastructure_issues=["missing tsconfig"],
            test_quality_issues=["bad assertion"],
            technical_issues=["wrong import"],
        )
        text = fb.to_feedback_text()
        assert "Infrastructure Issues" in text
        assert "missing tsconfig" in text
        assert "Test Quality Issues" in text
        assert "bad assertion" in text
        assert "Technical Issues" in text
        assert "wrong import" in text

    def test_to_feedback_text_empty_when_no_issues(self):
        fb = ExpertFeedback(solved=True, tests_passed=True, test_output="ok")
        assert fb.to_feedback_text() == ""


class TestEvaluateRepo:
    def test_returns_expert_feedback(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_RESPONSE), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            result = evaluate_repo(repo, tmp_path)

        assert isinstance(result, ExpertFeedback)

    def test_tests_passed_reflects_test_result(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_RESPONSE), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            result = evaluate_repo(repo, tmp_path)

        assert result.tests_passed is True

    def test_test_failure_captured(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_RESPONSE), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(False)):
            result = evaluate_repo(repo, tmp_path)

        assert result.tests_passed is False
        assert result.has_issues is True

    def test_issues_from_whitebox_captured(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_WITH_ISSUES), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            result = evaluate_repo(repo, tmp_path)

        assert "Missing tsconfig.json" in result.infrastructure_issues
        assert "Test assertions are too broad" in result.test_quality_issues
        assert "Import path is incorrect" in result.technical_issues

    def test_solution_files_populated(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_RESPONSE), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            result = evaluate_repo(repo, tmp_path)

        assert "src/ClickCounter.tsx" in result.solution_files

    def test_one_llm_call_made(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_expert.call_llm", return_value=EXPERT_WHITEBOX_RESPONSE) as mock_llm, \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            evaluate_repo(repo, tmp_path)

        assert mock_llm.call_count == 1

    def test_strips_markdown_fences_from_response(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")
        fenced = f"```json\n{EXPERT_WHITEBOX_RESPONSE}\n```"

        with patch("agents.student_expert.call_llm", return_value=fenced), \
             patch("agents.student_expert.run_tests", return_value=_make_test_result(True)):
            result = evaluate_repo(repo, tmp_path)

        assert isinstance(result, ExpertFeedback)


class TestSaveReferenceSolution:
    def test_creates_solution_directory(self, tmp_path):
        ref_dir = tmp_path / "reference_solutions"
        save_reference_solution({"src/main.py": "code"}, ref_dir, "my-repo")
        assert (ref_dir / "my-repo").is_dir()

    def test_writes_solution_files(self, tmp_path):
        ref_dir = tmp_path / "reference_solutions"
        solution = {
            "src/ClickCounter.tsx": "// solution",
            "src/utils.ts": "// utils",
        }
        save_reference_solution(solution, ref_dir, "click-counter")
        assert (ref_dir / "click-counter" / "src" / "ClickCounter.tsx").read_text() == "// solution"
        assert (ref_dir / "click-counter" / "src" / "utils.ts").read_text() == "// utils"

    def test_creates_nested_directories(self, tmp_path):
        ref_dir = tmp_path / "ref"
        save_reference_solution({"deep/nested/file.py": "content"}, ref_dir, "repo")
        assert (ref_dir / "repo" / "deep" / "nested" / "file.py").read_text() == "content"
