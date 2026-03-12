"""Tests for tools/llm_client.py"""

from unittest.mock import MagicMock, patch

import pytest

import config
from tools import token_tracker
from tools.llm_client import call_llm


class TestApiMode:
    def test_calls_anthropic_messages_create(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="the response")]

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            result = call_llm(
                system="You are helpful.",
                user="Hello",
                model="claude-sonnet-4-6",
                max_tokens=100,
            )

        assert result == "the response"
        mock_client.messages.create.assert_called_once()

    def test_passes_correct_args_to_api(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="ok")]

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            call_llm(
                system="sys prompt",
                user="user msg",
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
            )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["system"] == "sys prompt"
        assert call_kwargs["messages"] == [{"role": "user", "content": "user msg"}]

    def test_records_exact_token_counts_from_response_usage(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="hello")]
        mock_response.usage.input_tokens = 123
        mock_response.usage.output_tokens = 45
        mock_client.messages.create.return_value = mock_response

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="Builder")

        usage = token_tracker.get_usage()
        assert "Builder" in usage
        assert usage["Builder"].input_tokens == 123
        assert usage["Builder"].output_tokens == 45
        assert usage["Builder"].calls == 1

    def test_accumulates_tokens_across_multiple_calls(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()

        def make_response(in_tok, out_tok):
            r = MagicMock()
            r.content = [MagicMock(text="ok")]
            r.usage.input_tokens = in_tok
            r.usage.output_tokens = out_tok
            return r

        mock_client.messages.create.side_effect = [
            make_response(100, 50),
            make_response(200, 80),
        ]

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="Builder")
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="Builder")

        usage = token_tracker.get_usage()["Builder"]
        assert usage.input_tokens == 300
        assert usage.output_tokens == 130
        assert usage.calls == 2

    def test_tracks_different_agents_separately(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()

        def make_response(in_tok, out_tok):
            r = MagicMock()
            r.content = [MagicMock(text="ok")]
            r.usage.input_tokens = in_tok
            r.usage.output_tokens = out_tok
            return r

        mock_client.messages.create.side_effect = [
            make_response(500, 200),
            make_response(100, 40),
        ]

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="Builder")
            call_llm(system="s", user="u", model="claude-haiku-4-5-20251001", max_tokens=100, agent="Recommender")

        usage = token_tracker.get_usage()
        assert usage["Builder"].input_tokens == 500
        assert usage["Recommender"].input_tokens == 100

    def test_api_mode_does_not_set_estimated_flag(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", False)
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="ok")]

        with patch("tools.llm_client.anthropic.Anthropic", return_value=mock_client):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="Builder")

        assert token_tracker.is_estimated() is False


class TestCliMode:
    def test_calls_subprocess_run(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "cli response\n"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            result = call_llm(
                system="sys",
                user="user",
                model="claude-sonnet-4-6",
                max_tokens=1000,
            )

        mock_run.assert_called_once()
        assert result == "cli response"  # stripped

    def test_cli_command_includes_print_flag(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "response"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100)

        cmd = mock_run.call_args.args[0]
        assert "--print" in cmd

    def test_cli_command_does_not_include_model(self, monkeypatch):
        """CLI uses the user's configured model, so --model flag is intentionally omitted."""
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "response"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="s", user="u", model="claude-haiku-4-5-20251001", max_tokens=100)

        cmd = mock_run.call_args.args[0]
        assert "--model" not in cmd

    def test_cli_raises_on_nonzero_exit(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = "command not found"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Claude CLI failed"):
                call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100)

    def test_system_prompt_included_in_stdin(self, monkeypatch):
        """System prompt and user message are combined and passed via stdin."""
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "ok"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="MY SYSTEM PROMPT", user="user msg", model="claude-sonnet-4-6", max_tokens=100)

        # The combined prompt is passed via stdin (input= kwarg), not as a positional arg
        call_kwargs = mock_run.call_args.kwargs
        combined_prompt = call_kwargs["input"]
        assert "MY SYSTEM PROMPT" in combined_prompt
        assert "user msg" in combined_prompt

    def test_cli_strips_anthropic_api_key_from_env(self, monkeypatch):
        """ANTHROPIC_API_KEY must not leak into the CLI process (placeholder key causes auth failure)."""
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-placeholder")
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "ok"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100)

        call_kwargs = mock_run.call_args.kwargs
        assert "ANTHROPIC_API_KEY" not in call_kwargs["env"]

    def test_cli_records_estimated_token_counts(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        # 40-char output → 10 estimated output tokens
        mock_proc.stdout = "A" * 40

        system = "S" * 20
        user = "U" * 20
        # combined = "<system>\n" + system + "\n</system>\n\n" + user
        # = 9 + 20 + 12 + 20 = 61 chars → 15 estimated input tokens
        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            call_llm(system=system, user=user, model="claude-sonnet-4-6", max_tokens=100, agent="Builder")

        usage = token_tracker.get_usage()
        assert "Builder" in usage
        assert usage["Builder"].calls == 1
        # Verify estimates are char_count // 4 (non-zero, positive)
        assert usage["Builder"].input_tokens > 0
        assert usage["Builder"].output_tokens > 0

    def test_cli_mode_sets_estimated_flag(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "response"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100)

        assert token_tracker.is_estimated() is True

    def test_cli_estimated_input_tokens_from_combined_prompt(self, monkeypatch):
        """Input token estimate = len(combined_prompt) // 4."""
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = ""

        system = "X" * 100
        user = "Y" * 100
        # combined = "<system>\n" + "X"*100 + "\n</system>\n\n" + "Y"*100
        # = 9 + 100 + 12 + 100 = 221 chars → 221 // 4 = 55 estimated input tokens
        expected_combined = f"<system>\n{system}\n</system>\n\n{user}"
        expected_input = len(expected_combined) // 4

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            call_llm(system=system, user=user, model="claude-sonnet-4-6", max_tokens=100, agent="TestAgent")

        assert token_tracker.get_usage()["TestAgent"].input_tokens == expected_input

    def test_cli_estimated_output_tokens_from_response(self, monkeypatch):
        """Output token estimate = len(response) // 4."""
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Z" * 80 + "\n"  # stripped → 80 chars → 20 tokens

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100, agent="TestAgent")

        assert token_tracker.get_usage()["TestAgent"].output_tokens == 80 // 4
