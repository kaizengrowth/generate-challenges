"""Tests for agents/orchestrator.py"""

import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import config
from agents.builder import BuildResult, ChallengeRepo
from agents.orchestrator import RepoOutcome, RunResult, run_pipeline
from agents.student_expert import ExpertFeedback
from agents.student_novice import NoviceFeedback
from tests.conftest import (
    make_build_result,
    make_challenge_repo,
    make_expert_feedback,
    make_novice_feedback,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_write_repos_side_effect(output_dir: Path):
    """Returns a side_effect that creates the repo directory and returns its path."""
    call_count = [0]

    def _write(build_result, out_dir):
        call_count[0] += 1
        repo = build_result.repos[0]
        path = out_dir / repo.name
        path.mkdir(parents=True, exist_ok=True)
        return [path]

    return _write


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSkipRefineMode:
    def test_skip_refine_calls_only_builder(self, tmp_path):
        build_result = make_build_result()

        with patch("agents.orchestrator.build_challenges", return_value=build_result) as mock_build, \
             patch("agents.orchestrator.write_repos") as mock_write, \
             patch("agents.orchestrator.expert_evaluate") as mock_expert, \
             patch("agents.orchestrator.novice_evaluate") as mock_novice:
            mock_write.return_value = [tmp_path / "click-counter"]

            run_pipeline(
                challenge_descriptions=["Build a counter"],
                topic="React",
                output_dir=tmp_path / "output",
                skip_refine=True,
            )

        mock_build.assert_called_once()
        mock_write.assert_called_once()
        mock_expert.assert_not_called()
        mock_novice.assert_not_called()

    def test_skip_refine_returns_run_result(self, tmp_path):
        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", return_value=[tmp_path / "repo"]):
            result = run_pipeline(
                challenge_descriptions=["Build a counter"],
                topic="React",
                output_dir=tmp_path / "output",
                skip_refine=True,
            )
        assert isinstance(result, RunResult)


class TestHappyPath:
    def test_single_iteration_when_no_issues(self, tmp_path):
        out = tmp_path / "output"
        build_result = make_build_result()
        expert_fb = make_expert_feedback(tests_passed=True)
        novice_fb = make_novice_feedback(clarity_score=5)

        with patch("agents.orchestrator.build_challenges", return_value=build_result) as mock_build, \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb), \
             patch("agents.orchestrator.novice_evaluate", return_value=novice_fb), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(["Build a counter"], topic="React", output_dir=out)

        # Builder called once only (no refinement)
        assert mock_build.call_count == 1
        assert len(result.outcomes) == 1
        assert result.outcomes[0].iterations == 1

    def test_outcomes_populated(self, tmp_path):
        out = tmp_path / "output"
        build_result = make_build_result()
        expert_fb = make_expert_feedback(tests_passed=True)
        novice_fb = make_novice_feedback(clarity_score=5)

        with patch("agents.orchestrator.build_challenges", return_value=build_result), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb), \
             patch("agents.orchestrator.novice_evaluate", return_value=novice_fb), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(["Build a counter"], topic="React", output_dir=out)

        outcome = result.outcomes[0]
        assert isinstance(outcome, RepoOutcome)
        assert outcome.expert_feedback is expert_fb
        assert outcome.novice_feedback is novice_fb

    def test_reference_solution_saved(self, tmp_path):
        out = tmp_path / "output"
        expert_fb = make_expert_feedback(tests_passed=True)

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.save_reference_solution") as mock_save:
            run_pipeline(["Build a counter"], topic="React", output_dir=out)

        mock_save.assert_called_once()

    def test_iteration_log_written(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=make_expert_feedback()), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(["Build a counter"], topic="React", output_dir=out)

        log_path = out / "iteration_log.json"
        assert log_path.exists()
        log = json.loads(log_path.read_text())
        assert isinstance(log, list)
        assert len(log) == 1


class TestRefinementLoop:
    def test_expert_issues_trigger_second_build(self, tmp_path):
        out = tmp_path / "output"
        build_result = make_build_result()
        expert_fb_bad = make_expert_feedback(tests_passed=False)
        expert_fb_good = make_expert_feedback(tests_passed=True)
        novice_fb = make_novice_feedback(clarity_score=5)

        with patch("agents.orchestrator.build_challenges", return_value=build_result) as mock_build, \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", side_effect=[expert_fb_bad, expert_fb_good]), \
             patch("agents.orchestrator.novice_evaluate", return_value=novice_fb), \
             patch("agents.orchestrator.read_repo_files", return_value={}), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, max_iterations=3
            )

        assert mock_build.call_count == 2  # initial + one refinement
        assert result.outcomes[0].iterations == 2

    def test_novice_issues_trigger_refinement(self, tmp_path):
        out = tmp_path / "output"
        expert_fb = make_expert_feedback(tests_passed=True)
        novice_fb_bad = make_novice_feedback(clarity_score=2, confusion_points=["confusing"])
        novice_fb_good = make_novice_feedback(clarity_score=5)

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()) as mock_build, \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb), \
             patch("agents.orchestrator.novice_evaluate", side_effect=[novice_fb_bad, novice_fb_good]), \
             patch("agents.orchestrator.read_repo_files", return_value={}), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, max_iterations=3
            )

        assert mock_build.call_count == 2

    def test_stops_at_max_iterations(self, tmp_path):
        out = tmp_path / "output"
        # Always return failing feedback
        expert_fb_bad = make_expert_feedback(tests_passed=False)

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()) as mock_build, \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb_bad), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.read_repo_files", return_value={}), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, max_iterations=2
            )

        # Initial build + 1 refinement (max_iterations=2 means 2 student passes, 2 builds)
        assert mock_build.call_count == 2
        assert result.outcomes[0].iterations == 2

    def test_feedback_text_sent_to_builder_on_revision(self, tmp_path):
        out = tmp_path / "output"
        expert_fb_bad = make_expert_feedback(
            tests_passed=False,
            technical_issues=["import path is wrong"],
        )
        expert_fb_good = make_expert_feedback(tests_passed=True)

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()) as mock_build, \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", side_effect=[expert_fb_bad, expert_fb_good]), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.read_repo_files", return_value={}), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, max_iterations=3
            )

        # Second build call should include revision_feedback
        second_call_kwargs = mock_build.call_args_list[1].kwargs
        assert "revision_feedback" in second_call_kwargs
        assert second_call_kwargs["revision_feedback"]  # non-empty


class TestSkipNovice:
    def test_novice_not_called_when_skipped(self, tmp_path):
        out = tmp_path / "output"

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=make_expert_feedback()), \
             patch("agents.orchestrator.novice_evaluate") as mock_novice, \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, skip_novice=True
            )

        mock_novice.assert_not_called()

    def test_outcome_has_default_novice_feedback_when_skipped(self, tmp_path):
        out = tmp_path / "output"

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=make_expert_feedback()), \
             patch("agents.orchestrator.novice_evaluate"), \
             patch("agents.orchestrator.save_reference_solution"):
            result = run_pipeline(
                ["Build a counter"], topic="React", output_dir=out, skip_novice=True
            )

        # Default novice feedback should be non-problematic
        assert result.outcomes[0].novice_feedback.clarity_score == 5


class TestLessonsLearned:
    def test_lessons_learned_updated_when_issues(self, tmp_path):
        out = tmp_path / "output"
        expert_fb = make_expert_feedback(
            tests_passed=True,
            technical_issues=["import path wrong"],
        )

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=expert_fb), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(["Build a counter"], topic="React hooks", output_dir=out)

        content = config.LESSONS_LEARNED.read_text()
        assert "React hooks" in content

    def test_lessons_learned_not_updated_when_clean(self, tmp_path):
        out = tmp_path / "output"
        initial_content = config.LESSONS_LEARNED.read_text()

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=make_expert_feedback()), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(["Build a counter"], topic="React hooks", output_dir=out)

        # No new content added when there are no issues
        final_content = config.LESSONS_LEARNED.read_text()
        assert final_content == initial_content


class TestIterationLog:
    def test_log_entries_per_iteration(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        expert_bad = make_expert_feedback(tests_passed=False)
        expert_good = make_expert_feedback(tests_passed=True)

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", side_effect=[expert_bad, expert_good]), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.read_repo_files", return_value={}), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(["Build a counter"], topic="React", output_dir=out, max_iterations=3)

        log = json.loads((out / "iteration_log.json").read_text())
        assert len(log) == 2  # one entry per iteration

    def test_log_entry_structure(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()

        with patch("agents.orchestrator.build_challenges", return_value=make_build_result()), \
             patch("agents.orchestrator.write_repos", side_effect=_make_write_repos_side_effect(out)), \
             patch("agents.orchestrator.expert_evaluate", return_value=make_expert_feedback()), \
             patch("agents.orchestrator.novice_evaluate", return_value=make_novice_feedback()), \
             patch("agents.orchestrator.save_reference_solution"):
            run_pipeline(["Build a counter"], topic="React", output_dir=out)

        entry = json.loads((out / "iteration_log.json").read_text())[0]
        assert "repo" in entry
        assert "iteration" in entry
        assert "tests_passed" in entry
        assert "novice_clarity" in entry
