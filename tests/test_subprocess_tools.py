"""Tests for tools/subprocess_tools.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.subprocess_tools import TestResult, run_tests


def _mock_proc(returncode: int, stdout: str = "", stderr: str = "") -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestTestResult:
    def test_passed_true_on_zero_exit(self):
        r = TestResult(exit_code=0, stdout="ok", stderr="", combined="ok")
        assert r.passed is True

    def test_passed_false_on_nonzero_exit(self):
        r = TestResult(exit_code=1, stdout="", stderr="fail", combined="fail")
        assert r.passed is False

    def test_passed_false_on_any_nonzero(self):
        for code in [1, 2, 127, 255]:
            r = TestResult(exit_code=code, stdout="", stderr="", combined="")
            assert r.passed is False


class TestRunTests:
    def test_returns_passing_result_when_both_succeed(self, tmp_path):
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.return_value = _mock_proc(0, stdout="All passed", stderr="")
            result = run_tests(tmp_path, "npm install", "npm test")
        assert result.passed is True

    def test_returns_failing_result_when_tests_fail(self, tmp_path):
        install_proc = _mock_proc(0, stdout="installed", stderr="")
        test_proc = _mock_proc(1, stdout="", stderr="3 failed")
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.side_effect = [install_proc, test_proc]
            result = run_tests(tmp_path, "npm install", "npm test")
        assert result.passed is False
        assert result.exit_code == 1

    def test_short_circuits_on_install_failure(self, tmp_path):
        install_proc = _mock_proc(1, stdout="", stderr="ENOENT")
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.return_value = install_proc
            result = run_tests(tmp_path, "npm install", "npm test")
        # Only install should have been called
        assert mock_run.call_count == 1
        assert result.passed is False
        assert "INSTALL FAILED" in result.combined

    def test_captures_stdout_and_stderr(self, tmp_path):
        install_proc = _mock_proc(0)
        test_proc = _mock_proc(1, stdout="some output", stderr="some error")
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.side_effect = [install_proc, test_proc]
            result = run_tests(tmp_path, "pip install -r requirements.txt", "pytest -x")
        assert result.stdout == "some output"
        assert result.stderr == "some error"
        assert "some output" in result.combined
        assert "some error" in result.combined

    def test_runs_in_repo_dir(self, tmp_path):
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.return_value = _mock_proc(0)
            run_tests(tmp_path, "npm install", "npm test")
        for c in mock_run.call_args_list:
            assert c.kwargs.get("cwd") == tmp_path

    def test_uses_shell_true(self, tmp_path):
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.return_value = _mock_proc(0)
            run_tests(tmp_path, "npm install", "npm test")
        for c in mock_run.call_args_list:
            assert c.kwargs.get("shell") is True

    def test_sets_ci_true_in_env(self, tmp_path):
        """CI=true prevents Jest and other runners from entering watch mode."""
        with patch("tools.subprocess_tools.subprocess.run") as mock_run:
            mock_run.return_value = _mock_proc(0)
            run_tests(tmp_path, "npm install", "npm test")
        for c in mock_run.call_args_list:
            assert c.kwargs.get("env", {}).get("CI") == "true"
