"""Run test commands inside challenge repos and capture output."""

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
    """
    # Install dependencies
    install_result = subprocess.run(
        install_command,
        shell=True,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=120,
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
        timeout=120,
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
