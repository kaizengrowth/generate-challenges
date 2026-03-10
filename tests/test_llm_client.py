"""Tests for tools/llm_client.py"""

from unittest.mock import MagicMock, patch

import pytest

import config
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

    def test_cli_command_includes_model(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "response"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="s", user="u", model="claude-haiku-4-5-20251001", max_tokens=100)

        cmd = mock_run.call_args.args[0]
        assert "--model" in cmd
        assert "claude-haiku-4-5-20251001" in cmd

    def test_cli_raises_on_nonzero_exit(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = "command not found"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="Claude CLI failed"):
                call_llm(system="s", user="u", model="claude-sonnet-4-6", max_tokens=100)

    def test_system_prompt_included_in_message(self, monkeypatch):
        monkeypatch.setattr(config, "USE_CLAUDE_CLI", True)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "ok"

        with patch("tools.llm_client.subprocess.run", return_value=mock_proc) as mock_run:
            call_llm(system="MY SYSTEM PROMPT", user="user msg", model="claude-sonnet-4-6", max_tokens=100)

        # The combined prompt (last arg in the CLI command) should contain the system prompt
        cmd = mock_run.call_args.args[0]
        combined_prompt = cmd[-1]
        assert "MY SYSTEM PROMPT" in combined_prompt
        assert "user msg" in combined_prompt
