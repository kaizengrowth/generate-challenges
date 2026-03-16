"""Tests for agents/builder.py"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import config
from agents.builder import (
    BuildResult,
    ChallengeRepo,
    build_challenges,
    write_repos,
)
from tests.conftest import (
    PLANNER_RESPONSE,
    PLANNER_RESPONSE_WITH_NOTES,
    GENERATOR_RESPONSE,
)


# Helpers to build two-call side_effect lists for the normal flow
# (plan_challenges call + generate_repo call).
def _normal_side_effect():
    return [PLANNER_RESPONSE, GENERATOR_RESPONSE]

def _notes_side_effect():
    return [PLANNER_RESPONSE_WITH_NOTES, GENERATOR_RESPONSE]


class TestBuildChallenges:
    def test_returns_build_result(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            result = build_challenges(["Build a click counter"])
        assert isinstance(result, BuildResult)

    def test_repos_contain_challenge_repo(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            result = build_challenges(["Build a click counter"])
        assert len(result.repos) == 1
        assert isinstance(result.repos[0], ChallengeRepo)

    def test_repo_fields_populated(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            result = build_challenges(["Build a click counter"])
        repo = result.repos[0]
        assert repo.name == "click-counter"
        assert repo.description == "A React click counter challenge"
        assert repo.challenges == ["Click Counter"]
        assert repo.install_command == "npm install"
        assert repo.test_command == "npm test"

    def test_repo_files_populated(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            result = build_challenges(["Build a click counter"])
        assert "README.md" in result.repos[0].files
        assert "src/ClickCounter.tsx" in result.repos[0].files

    def test_strips_markdown_fences(self):
        fenced_plan = f"```json\n{PLANNER_RESPONSE}\n```"
        fenced_gen = f"```json\n{GENERATOR_RESPONSE}\n```"
        with patch("agents.builder.call_llm", side_effect=[fenced_plan, fenced_gen]), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            result = build_challenges(["Build a click counter"])
        assert len(result.repos) == 1

    def test_passes_descriptions_to_llm(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()) as mock_llm, \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Build a click counter", "Build a toggle"])
        # Descriptions go into the planner call (first LLM call)
        planner_user_msg = mock_llm.call_args_list[0].kwargs["user"]
        assert "Build a click counter" in planner_user_msg
        assert "Build a toggle" in planner_user_msg

    def test_passes_instructor_notes_to_llm(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()) as mock_llm, \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Build something"], instructor_notes="Focus on TypeScript")
        # Notes go into the planner call (first LLM call)
        planner_user_msg = mock_llm.call_args_list[0].kwargs["user"]
        assert "Focus on TypeScript" in planner_user_msg

    def test_passes_revision_feedback_to_llm(self):
        # Revision path requires both revision_feedback AND prior_files.
        prior = {"click-counter": {"README.md": "old readme"}}
        with patch("agents.builder.call_llm", return_value=GENERATOR_RESPONSE) as mock_llm, \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(
                ["Build something"],
                revision_feedback="Tests are broken — fix the import paths",
                prior_files=prior,
            )
        # Revision uses a single targeted LLM call (_revise_repo)
        user_msg = mock_llm.call_args.kwargs["user"]
        assert "Tests are broken" in user_msg

    def test_saves_challenge_type_notes_to_knowledge_base(self):
        with patch("agents.builder.call_llm", side_effect=_notes_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Fix the bug"], topic="debugging")

        # KB file should have been created
        kb_files = list(config.CHALLENGE_TYPES_DIR.glob("*.md"))
        assert len(kb_files) == 1
        assert "For debugging challenges" in kb_files[0].read_text()

    def test_skips_empty_challenge_type_notes(self):
        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Build something"], topic="react")

        # No KB file should have been created (notes were empty)
        kb_files = list(config.CHALLENGE_TYPES_DIR.glob("*.md"))
        assert len(kb_files) == 0

    def test_appends_to_existing_kb_file(self):
        existing = config.CHALLENGE_TYPES_DIR / "debugging.md"
        existing.write_text("# Debugging\n\nOld content.")

        with patch("agents.builder.call_llm", side_effect=_notes_side_effect()), \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Fix the bug"], topic="debugging")

        content = existing.read_text()
        assert "Old content." in content
        assert "For debugging challenges" in content

    def test_knowledge_base_loaded_into_prompt(self):
        # Write a KB file to simulate existing knowledge
        (config.CHALLENGE_TYPES_DIR / "react.md").write_text("React KB content here.")

        with patch("agents.builder.call_llm", side_effect=_normal_side_effect()) as mock_llm, \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(["Build something"], topic="react")

        # KB is injected into the planner call (first LLM call)
        planner_user_msg = mock_llm.call_args_list[0].kwargs["user"]
        assert "React KB content here." in planner_user_msg

    def test_prior_files_included_in_revision_prompt(self):
        prior = {"click-counter": {"README.md": "old readme"}}
        with patch("agents.builder.call_llm", return_value=GENERATOR_RESPONSE) as mock_llm, \
             patch("agents.builder._load_filtered_reference_docs", return_value=""):
            build_challenges(
                ["Build something"],
                revision_feedback="Fix it",
                prior_files=prior,
            )
        user_msg = mock_llm.call_args.kwargs["user"]
        assert "old readme" in user_msg


class TestWriteRepos:
    def test_creates_repo_directory(self, tmp_path):
        build_result = BuildResult(repos=[
            ChallengeRepo(
                name="my-repo",
                description="Test",
                challenges=["C1"],
                install_command="npm install",
                test_command="npm test",
                files={"README.md": "# Test"},
            )
        ])
        with patch("agents.builder.git_init"):
            write_repos(build_result, tmp_path)
        assert (tmp_path / "my-repo").is_dir()

    def test_writes_all_files(self, tmp_path):
        files = {"README.md": "readme", "src/index.ts": "code"}
        build_result = BuildResult(repos=[
            ChallengeRepo(
                name="repo",
                description="Test",
                challenges=["C1"],
                install_command="npm install",
                test_command="npm test",
                files=files,
            )
        ])
        with patch("agents.builder.git_init"):
            write_repos(build_result, tmp_path)
        assert (tmp_path / "repo" / "README.md").read_text() == "readme"
        assert (tmp_path / "repo" / "src" / "index.ts").read_text() == "code"

    def test_calls_git_init_for_each_repo(self, tmp_path):
        repos = [
            ChallengeRepo("repo-a", "A", ["C1"], "npm install", "npm test", {"f.txt": "a"}),
            ChallengeRepo("repo-b", "B", ["C2"], "npm install", "npm test", {"f.txt": "b"}),
        ]
        build_result = BuildResult(repos=repos)
        with patch("agents.builder.git_init") as mock_git:
            write_repos(build_result, tmp_path)
        assert mock_git.call_count == 2

    def test_returns_list_of_paths(self, tmp_path):
        build_result = BuildResult(repos=[
            ChallengeRepo("repo", "D", ["C1"], "npm install", "npm test", {"f.txt": "x"})
        ])
        with patch("agents.builder.git_init"):
            paths = write_repos(build_result, tmp_path)
        assert len(paths) == 1
        assert paths[0] == tmp_path / "repo"
