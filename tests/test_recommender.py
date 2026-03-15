"""Tests for agents/recommender.py"""

from unittest.mock import patch

import pytest

from agents.recommender import ChallengeCandidate, recommend_challenges
from tests.conftest import RECOMMENDER_RESPONSE


class TestRecommendChallenges:
    def test_returns_list_of_candidates(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE):
            result = recommend_challenges("React state management")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_candidates_are_correct_type(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE):
            result = recommend_challenges("React")
        for candidate in result:
            assert isinstance(candidate, ChallengeCandidate)

    def test_candidate_fields_populated(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE):
            result = recommend_challenges("React")
        first = result[0]
        assert first.title == "Click Counter"
        assert first.description == "Build a button that increments a displayed count"
        assert first.learning_objective == "Practice useState hook"
        assert first.difficulty == "beginner"
        assert first.challenge_type == "implementation"

    def test_passes_topic_to_llm(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE) as mock_llm:
            recommend_challenges("Python decorators")
        user_arg = mock_llm.call_args.kwargs["user"]
        assert "Python decorators" in user_arg

    def test_passes_extra_context_to_llm(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE) as mock_llm:
            recommend_challenges("React", extra_context="Focus on hooks")
        user_arg = mock_llm.call_args.kwargs["user"]
        assert "Focus on hooks" in user_arg

    def test_no_extra_context_omitted_from_prompt(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE) as mock_llm:
            recommend_challenges("React")
        user_arg = mock_llm.call_args.kwargs["user"]
        assert "Additional context" not in user_arg

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{RECOMMENDER_RESPONSE}\n```"
        with patch("agents.recommender.call_llm", return_value=fenced):
            result = recommend_challenges("React")
        assert len(result) == 3  # still parsed correctly

    def test_all_difficulties_parsed(self):
        with patch("agents.recommender.call_llm", return_value=RECOMMENDER_RESPONSE):
            result = recommend_challenges("React")
        difficulties = {c.difficulty for c in result}
        assert "beginner" in difficulties
        assert "intermediate" in difficulties
