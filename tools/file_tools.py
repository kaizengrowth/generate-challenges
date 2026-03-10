"""Utilities for reading and writing challenge files."""

from pathlib import Path


def read_file(path: Path) -> str:
    """Read a file, returning empty string if it doesn't exist."""
    if path.exists():
        return path.read_text()
    return ""


def write_repo_files(repo_dir: Path, files: dict[str, str]) -> None:
    """Write a dict of {relative_path: content} into repo_dir."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    for rel_path, content in files.items():
        dest = repo_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)


def read_repo_files(repo_dir: Path) -> dict[str, str]:
    """Read all text files from a repo directory into a dict."""
    files = {}
    for path in sorted(repo_dir.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(repo_dir)
            try:
                files[str(rel)] = path.read_text()
            except (UnicodeDecodeError, PermissionError):
                pass  # Skip binary or unreadable files
    return files


def format_files_for_prompt(files: dict[str, str]) -> str:
    """Format a file dict as a readable block for LLM prompts."""
    parts = []
    for path, content in files.items():
        parts.append(f"=== {path} ===\n{content}")
    return "\n\n".join(parts)
