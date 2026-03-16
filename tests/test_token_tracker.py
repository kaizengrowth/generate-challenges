"""Tests for tools/token_tracker.py"""

from tools import token_tracker
from tools.token_tracker import AgentTokenUsage


class TestAgentTokenUsage:
    def test_total_tokens_sums_input_and_output(self):
        u = AgentTokenUsage(input_tokens=300, output_tokens=100, calls=1)
        assert u.total_tokens == 400

    def test_defaults_are_zero(self):
        u = AgentTokenUsage()
        assert u.input_tokens == 0
        assert u.output_tokens == 0
        assert u.calls == 0
        assert u.total_tokens == 0


class TestRecord:
    def test_record_accumulates_for_same_agent(self):
        token_tracker.record("Builder", input_tokens=100, output_tokens=50)
        token_tracker.record("Builder", input_tokens=200, output_tokens=75)

        usage = token_tracker.get_usage()
        assert usage["Builder"].input_tokens == 300
        assert usage["Builder"].output_tokens == 125
        assert usage["Builder"].calls == 2

    def test_record_tracks_different_agents_separately(self):
        token_tracker.record("Builder", input_tokens=1000, output_tokens=500)
        token_tracker.record("Recommender", input_tokens=200, output_tokens=100)

        usage = token_tracker.get_usage()
        assert usage["Builder"].input_tokens == 1000
        assert usage["Recommender"].input_tokens == 200

    def test_record_increments_call_count(self):
        token_tracker.record("Expert Student", input_tokens=1, output_tokens=1)
        token_tracker.record("Expert Student", input_tokens=1, output_tokens=1)
        token_tracker.record("Expert Student", input_tokens=1, output_tokens=1)

        assert token_tracker.get_usage()["Expert Student"].calls == 3


class TestTotals:
    def test_totals_sums_all_agents(self):
        token_tracker.record("Builder", input_tokens=1000, output_tokens=500)
        token_tracker.record("Recommender", input_tokens=200, output_tokens=100)
        token_tracker.record("Expert Student", input_tokens=300, output_tokens=150)

        t = token_tracker.totals()
        assert t.input_tokens == 1500
        assert t.output_tokens == 750
        assert t.total_tokens == 2250
        assert t.calls == 3

    def test_totals_returns_zeros_when_empty(self):
        t = token_tracker.totals()
        assert t.input_tokens == 0
        assert t.output_tokens == 0
        assert t.calls == 0


class TestEstimatedFlag:
    def test_not_estimated_by_default(self):
        assert token_tracker.is_estimated() is False

    def test_set_estimated_true(self):
        token_tracker.set_estimated(True)
        assert token_tracker.is_estimated() is True

    def test_set_estimated_false(self):
        token_tracker.set_estimated(True)
        token_tracker.set_estimated(False)
        assert token_tracker.is_estimated() is False


class TestReset:
    def test_reset_clears_usage(self):
        token_tracker.record("Builder", input_tokens=999, output_tokens=999)
        token_tracker.reset()
        assert token_tracker.get_usage() == {}

    def test_reset_clears_estimated_flag(self):
        token_tracker.set_estimated(True)
        token_tracker.reset()
        assert token_tracker.is_estimated() is False

    def test_reset_totals_returns_zeros(self):
        token_tracker.record("Builder", input_tokens=500, output_tokens=200)
        token_tracker.reset()
        t = token_tracker.totals()
        assert t.total_tokens == 0
