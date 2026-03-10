"""Tests for tools/file_tools.py"""

from pathlib import Path

import pytest

from tools.file_tools import (
    format_files_for_prompt,
    read_file,
    read_repo_files,
    write_repo_files,
)


class TestReadFile:
    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        assert read_file(f) == "hello world"

    def test_returns_empty_string_for_missing_file(self, tmp_path):
        assert read_file(tmp_path / "nonexistent.txt") == ""

    def test_reads_multiline_file(self, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("line1\nline2\nline3")
        assert read_file(f) == "line1\nline2\nline3"


class TestWriteRepoFiles:
    def test_creates_files(self, tmp_path):
        files = {"README.md": "# Hello", "src/index.ts": "export {}"}
        write_repo_files(tmp_path, files)
        assert (tmp_path / "README.md").read_text() == "# Hello"
        assert (tmp_path / "src" / "index.ts").read_text() == "export {}"

    def test_creates_nested_directories(self, tmp_path):
        files = {"a/b/c/deep.txt": "deep content"}
        write_repo_files(tmp_path, files)
        assert (tmp_path / "a" / "b" / "c" / "deep.txt").read_text() == "deep content"

    def test_creates_output_dir_if_missing(self, tmp_path):
        dest = tmp_path / "new_dir"
        assert not dest.exists()
        write_repo_files(dest, {"file.txt": "content"})
        assert dest.exists()
        assert (dest / "file.txt").read_text() == "content"

    def test_overwrites_existing_file(self, tmp_path):
        (tmp_path / "file.txt").write_text("old content")
        write_repo_files(tmp_path, {"file.txt": "new content"})
        assert (tmp_path / "file.txt").read_text() == "new content"

    def test_handles_empty_file_dict(self, tmp_path):
        write_repo_files(tmp_path, {})  # should not raise


class TestReadRepoFiles:
    def test_reads_all_files(self, tmp_path):
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.ts").write_text("code")
        result = read_repo_files(tmp_path)
        assert result["README.md"] == "readme"
        assert result["src/index.ts"] == "code"

    def test_excludes_git_directory(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")
        (tmp_path / "README.md").write_text("readme")
        result = read_repo_files(tmp_path)
        assert "README.md" in result
        assert not any(".git" in k for k in result)

    def test_round_trip(self, tmp_path):
        # Use a clean subdirectory so the isolated_config fixture's KB files
        # (created in tmp_path) don't appear in the read results.
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        files = {
            "README.md": "# Test",
            "src/main.py": "print('hello')",
            "tests/test_main.py": "def test_one(): pass",
        }
        write_repo_files(repo_dir, files)
        result = read_repo_files(repo_dir)
        assert result == files

    def test_returns_empty_dict_for_empty_dir(self, tmp_path):
        empty = tmp_path / "empty_repo"
        empty.mkdir()
        assert read_repo_files(empty) == {}

    def test_skips_directories(self, tmp_path):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        (repo_dir / "subdir").mkdir()
        (repo_dir / "file.txt").write_text("content")
        result = read_repo_files(repo_dir)
        assert list(result.keys()) == ["file.txt"]


class TestFormatFilesForPrompt:
    def test_formats_single_file(self):
        files = {"README.md": "# Hello"}
        result = format_files_for_prompt(files)
        assert "=== README.md ===" in result
        assert "# Hello" in result

    def test_formats_multiple_files(self):
        files = {"a.txt": "aaa", "b.txt": "bbb"}
        result = format_files_for_prompt(files)
        assert "=== a.txt ===" in result
        assert "=== b.txt ===" in result
        assert "aaa" in result
        assert "bbb" in result

    def test_separates_files_with_blank_lines(self):
        files = {"a.txt": "aaa", "b.txt": "bbb"}
        result = format_files_for_prompt(files)
        # Files should be separated
        assert result.index("=== a.txt ===") < result.index("=== b.txt ===")

    def test_returns_empty_string_for_empty_dict(self):
        assert format_files_for_prompt({}) == ""
