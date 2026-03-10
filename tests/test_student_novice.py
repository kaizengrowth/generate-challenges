"""Tests for agents/student_novice.py"""

from pathlib import Path
from unittest.mock import patch

import pytest

from agents.builder import ChallengeRepo
from agents.student_novice import NoviceFeedback, evaluate_repo
from tests.conftest import (
    NOVICE_BLACKBOX_RESPONSE,
    NOVICE_WHITEBOX_RESPONSE,
    NOVICE_WHITEBOX_WITH_ISSUES,
    make_challenge_repo,
)


class TestNoviceFeedbackDataclass:
    def test_has_issues_false_when_clear(self):
        fb = NoviceFeedback(clarity_score=4, difficulty_assessment="appropriate")
        assert fb.has_issues is False

    def test_has_issues_false_at_exactly_four(self):
        fb = NoviceFeedback(clarity_score=4, difficulty_assessment="appropriate")
        assert fb.has_issues is False

    def test_has_issues_true_when_clarity_below_four(self):
        fb = NoviceFeedback(clarity_score=3, difficulty_assessment="appropriate")
        assert fb.has_issues is True

    def test_has_issues_true_when_confusion_points_present(self):
        fb = NoviceFeedback(
            clarity_score=5,
            difficulty_assessment="appropriate",
            confusion_points=["Unclear what memoization means"],
        )
        assert fb.has_issues is True

    def test_has_issues_true_when_missing_context(self):
        fb = NoviceFeedback(
            clarity_score=5,
            difficulty_assessment="appropriate",
            missing_context=["No example output shown"],
        )
        assert fb.has_issues is True

    def test_to_feedback_text_includes_score_and_difficulty(self):
        fb = NoviceFeedback(clarity_score=3, difficulty_assessment="too hard")
        text = fb.to_feedback_text()
        assert "3/5" in text
        assert "too hard" in text

    def test_to_feedback_text_includes_confusion_points(self):
        fb = NoviceFeedback(
            clarity_score=2,
            difficulty_assessment="appropriate",
            confusion_points=["Jargon not explained", "Ambiguous naming"],
        )
        text = fb.to_feedback_text()
        assert "Confusion Points" in text
        assert "Jargon not explained" in text
        assert "Ambiguous naming" in text

    def test_to_feedback_text_includes_missing_context(self):
        fb = NoviceFeedback(
            clarity_score=3,
            difficulty_assessment="appropriate",
            missing_context=["No example given"],
        )
        text = fb.to_feedback_text()
        assert "Missing Context" in text
        assert "No example given" in text

    def test_to_feedback_text_omits_empty_sections(self):
        fb = NoviceFeedback(clarity_score=5, difficulty_assessment="appropriate")
        text = fb.to_feedback_text()
        assert "Confusion Points" not in text
        assert "Missing Context" not in text


class TestEvaluateRepo:
    def test_returns_novice_feedback(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            result = evaluate_repo(repo, tmp_path, test_output="test output here")

        assert isinstance(result, NoviceFeedback)

    def test_clarity_score_populated(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            result = evaluate_repo(repo, tmp_path, test_output="")

        assert result.clarity_score == 4

    def test_difficulty_assessment_populated(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            result = evaluate_repo(repo, tmp_path, test_output="")

        assert result.difficulty_assessment == "appropriate"

    def test_issues_captured_from_whitebox(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_WITH_ISSUES, NOVICE_BLACKBOX_RESPONSE]
            result = evaluate_repo(repo, tmp_path, test_output="")

        assert result.clarity_score == 2
        assert result.difficulty_assessment == "too hard"
        assert "The term 'memoization' is not explained" in result.confusion_points
        assert "No example output provided" in result.missing_context

    def test_test_output_passed_to_blackbox_llm(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            evaluate_repo(repo, tmp_path, test_output="FAIL: expected 3 but got undefined")

        bb_call = mock_llm.call_args_list[1]
        assert "FAIL: expected 3 but got undefined" in bb_call.kwargs["user"]

    def test_two_llm_calls_made(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            evaluate_repo(repo, tmp_path, test_output="")

        assert mock_llm.call_count == 2

    def test_strips_markdown_fences(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")
        fenced_wb = f"```json\n{NOVICE_WHITEBOX_RESPONSE}\n```"
        fenced_bb = f"```json\n{NOVICE_BLACKBOX_RESPONSE}\n```"

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [fenced_wb, fenced_bb]
            result = evaluate_repo(repo, tmp_path, test_output="")

        assert isinstance(result, NoviceFeedback)

    def test_error_message_quality_from_blackbox(self, tmp_path):
        repo = make_challenge_repo()
        (tmp_path / "README.md").write_text("# Test")

        with patch("agents.student_novice.call_llm") as mock_llm:
            mock_llm.side_effect = [NOVICE_WHITEBOX_RESPONSE, NOVICE_BLACKBOX_RESPONSE]
            result = evaluate_repo(repo, tmp_path, test_output="")

        assert "Error messages are actionable" in result.error_message_quality
