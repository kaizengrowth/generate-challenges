"""Git repository initialization utilities."""

import subprocess
from pathlib import Path


def git_init(repo_dir: Path) -> None:
    """Initialize a git repo at repo_dir and make an initial commit."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial challenge scaffold"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        env={
            **__import__("os").environ,
            "GIT_AUTHOR_NAME": "Challenge Platform",
            "GIT_AUTHOR_EMAIL": "platform@codesmith.io",
            "GIT_COMMITTER_NAME": "Challenge Platform",
            "GIT_COMMITTER_EMAIL": "platform@codesmith.io",
        },
    )
