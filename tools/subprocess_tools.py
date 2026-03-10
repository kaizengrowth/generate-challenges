"""Run test commands inside challenge repos and capture output."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    exit_code: int
    stdout: str
    stderr: str
    combined: str  # stdout + stderr interleaved (best-effort)

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def run_tests(repo_dir: Path, install_command: str, test_command: str) -> TestResult:
    """
    Run install then test commands inside repo_dir.
    Returns a TestResult with captured output.

    CI=true is injected into the subprocess environment so that Jest (and
    most other test runners) run in non-interactive, single-pass mode and
    exit immediately rather than entering watch mode.
    """
    # Propagate current environment and force non-interactive / CI mode
    env = {**os.environ, "CI": "true"}

    # Install dependencies
    install_result = subprocess.run(
        install_command,
        shell=True,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    if install_result.returncode != 0:
        combined = (
            f"[INSTALL FAILED]\nstdout: {install_result.stdout}\nstderr: {install_result.stderr}"
        )
        return TestResult(
            exit_code=install_result.returncode,
            stdout=install_result.stdout,
            stderr=install_result.stderr,
            combined=combined,
        )

    # Run tests
    test_result = subprocess.run(
        test_command,
        shell=True,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    combined = ""
    if test_result.stdout:
        combined += test_result.stdout
    if test_result.stderr:
        combined += "\n" + test_result.stderr

    return TestResult(
        exit_code=test_result.returncode,
        stdout=test_result.stdout,
        stderr=test_result.stderr,
        combined=combined.strip(),
    )
