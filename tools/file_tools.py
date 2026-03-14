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


# Directories that should never be sent to the LLM (generated / dependency dirs)
_SKIP_DIRS = frozenset({
    "node_modules", ".next", "dist", "build", "target",
    "__pycache__", ".pytest_cache", "coverage", ".turbo",
    ".venv", "venv", ".gradle", ".mvn", ".cache",
})

# Lockfiles and other non-essential generated files
_SKIP_FILES = frozenset({
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", ".DS_Store",
})


def read_repo_files(repo_dir: Path) -> dict[str, str]:
    """Read source files from a repo directory into a dict, skipping generated content."""
    files = {}
    for path in sorted(repo_dir.rglob("*")):
        if not path.is_file():
            continue
        parts = path.parts
        if ".git" in parts:
            continue
        if any(part in _SKIP_DIRS for part in parts):
            continue
        if path.name in _SKIP_FILES:
            continue
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
