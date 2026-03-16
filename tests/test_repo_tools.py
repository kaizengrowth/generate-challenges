"""Tests for tools/repo_tools.py"""

from pathlib import Path
from unittest.mock import call, patch

import pytest

from tools.repo_tools import git_init


class TestGitInit:
    def test_creates_directory_if_missing(self, tmp_path):
        repo_dir = tmp_path / "new-repo"
        assert not repo_dir.exists()
        with patch("tools.repo_tools.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            git_init(repo_dir)
        assert repo_dir.exists()

    def test_runs_git_init(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        with patch("tools.repo_tools.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            git_init(repo_dir)
        calls = [c.args[0] for c in mock_run.call_args_list]
        assert ["git", "init"] in calls

    def test_runs_git_add_and_commit(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        with patch("tools.repo_tools.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            git_init(repo_dir)
        all_cmds = [c.args[0] for c in mock_run.call_args_list]
        assert ["git", "add", "."] in all_cmds
        assert any(c[0] == "git" and c[1] == "commit" for c in all_cmds)

    def test_runs_commands_in_repo_dir(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        with patch("tools.repo_tools.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            git_init(repo_dir)
        for c in mock_run.call_args_list:
            assert c.kwargs.get("cwd") == repo_dir

    def test_runs_exactly_three_commands(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        with patch("tools.repo_tools.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            git_init(repo_dir)
        assert mock_run.call_count == 3  # init, add, commit
