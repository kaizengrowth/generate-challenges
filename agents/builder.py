"""
Builder Agent — generates complete, runnable challenge repos from a challenge description.

Outputs one or more self-contained git repos (clustered when they share an ecosystem).
"""

import json
from dataclasses import dataclass
from pathlib import Path

import config
from tools.file_tools import read_file, write_repo_files, format_files_for_prompt
from tools.llm_client import call_llm, parse_json_from_response
from tools.repo_tools import git_init


@dataclass
class ChallengeRepo:
    name: str
    description: str
    challenges: list[str]
    install_command: str
    test_command: str
    files: dict[str, str]  # relative_path -> content


@dataclass
class BuildResult:
    repos: list[ChallengeRepo]


def _load_reference_docs() -> str:
    patterns = read_file(config.GENERATION_PATTERNS)
    templates = read_file(config.PROJECT_TEMPLATES)
    ui_styling = read_file(config.UI_STYLING)
    return (
        f"## Generation Patterns\n\n{patterns}\n\n"
        f"## Project Templates\n\n{templates}\n\n"
        f"## UI Styling Guide\n\n{ui_styling}"
    )


def _load_knowledge_base(topic: str) -> str:
    """Load any relevant knowledge base entries for this topic."""
    kb_parts = []

    # Load lessons learned
    lessons = read_file(config.LESSONS_LEARNED)
    if lessons.strip() and "Builder will append" not in lessons:
        kb_parts.append(f"## General Lessons Learned\n\n{lessons}")

    # Load any challenge type files
    if config.CHALLENGE_TYPES_DIR.exists():
        for type_file in sorted(config.CHALLENGE_TYPES_DIR.glob("*.md")):
            content = type_file.read_text()
            kb_parts.append(f"## Knowledge Base: {type_file.stem}\n\n{content}")

    return "\n\n".join(kb_parts)


def _load_knowledge_base_for_feedback(feedback_summary: str) -> str:
    """Load knowledge base when revising based on student feedback."""
    return _load_knowledge_base(feedback_summary)


BUILDER_SYSTEM_PROMPT = """You are an expert coding school challenge designer. Your job is to generate
complete, runnable coding challenges for bootcamp students.

You will receive:
- A challenge description (or list of challenge descriptions)
- Reference documentation on how to generate skeleton files and tests
- Optionally: knowledge base entries with templates for specific challenge types
- Optionally: feedback from student agents asking you to revise a previous attempt

Your output MUST be a single valid JSON object with this structure:

{
  "repos": [
    {
      "name": "kebab-case-repo-name",
      "description": "One sentence describing what this repo covers",
      "challenges": ["Challenge 1 name", "Challenge 2 name"],
      "install_command": "npm install",
      "test_command": "npm test",
      "files": {
        "README.md": "...",
        "package.json": "...",
        "src/ClickCounter.tsx": "...",
        "tests/ClickCounter.test.tsx": "...",
        ".gitignore": "..."
      }
    }
  ],
  "clustering_rationale": "Brief explanation of why you split into N repos",
  "challenge_type_notes": "If this is a new/unusual challenge type, describe your approach here so it can be saved to the knowledge base"
}

## Clustering Rules
- Group challenges into ONE repo when they share the same language, framework, build system, and logical theme
- Create SEPARATE repos when challenges have incompatible ecosystems, very different setups, or are standalone modules
- Never mix languages in one repo (no Python + JS in the same package.json project)

## Challenge Quality Rules
- Skeleton files: give shape without logic. Empty functions, stub methods, placeholder returns
- Test files: tests START FAILING. They turn green as students implement. Never pre-solve anything
- Test progression: existence/smoke → initial state → basic behavior → return values → edge cases
- Stop tests on first failure (--bail 1 for vitest, -x for pytest, etc.)
- Every repo must be fully self-contained and runnable with just install + test commands
- Include .gitignore appropriate for the ecosystem

## Browser Visualization Rules (UI challenges: React, Vue, Angular)
- ALWAYS generate the browser entry files so `npm run dev` / `ng serve` works out of the box
- React: generate `index.html`, `src/main.tsx`, and `src/App.tsx`
- Vue: generate `index.html`, `src/main.ts`, and `src/App.vue`
- Angular: generate `src/index.html`, `src/main.ts`, `src/app/app.module.ts`, `src/app/app.component.ts`, and `angular.json`
- `src/App.tsx` / `src/App.vue` / `src/app/app.component.ts` must import and render EVERY challenge component in its own labeled `<section>`, so students can see their work in a browser immediately
- These entry files are required infrastructure — include them in addition to the skeleton and test files

## Debugging Challenge Rules (when applicable)
- Provide intentionally broken code (logic bugs, not syntax errors)
- Tests should pass ONLY when the bugs are fixed
- The README describes only the incorrect behavior the student will observe (e.g., "the function returns undefined instead of the expected value") — do NOT hint at the cause or the fix
- Do NOT add bug comments or annotations in the code; the student must locate and diagnose the issue themselves

## Output Requirements
- Output ONLY a single, valid JSON object — nothing else
- Do NOT wrap JSON in markdown code fences
- Do NOT add explanatory text before or after the JSON
- All file contents must be complete and valid — no placeholders like "..." inside file content
- Escape all special characters in JSON strings properly
- Ensure the entire response is valid, parseable JSON that starts with { and ends with }
"""


def build_challenges(
    challenge_descriptions: list[str],
    topic: str = "",
    instructor_notes: str = "",
    revision_feedback: str = "",
    prior_files: dict[str, dict[str, str]] | None = None,
    amend_instructions: str = "",
) -> BuildResult:
    """
    Generate challenge repos from a list of challenge descriptions.

    Args:
        challenge_descriptions: list of challenge descriptions to implement
        topic: the broader topic (used to look up knowledge base)
        instructor_notes: any additional guidance from the instructor
        revision_feedback: structured feedback from student agents (for refinement iterations)
        prior_files: files from a previous build attempt (for refinement or amend context)
        amend_instructions: when set, instructs the builder to amend existing repos rather
                            than generate from scratch; prior_files holds the existing repos
    """
    ref_docs = _load_reference_docs()
    kb = _load_knowledge_base(topic)

    # Build the user message
    parts = []

    if amend_instructions:
        parts.append(
            "## Amendment Mode\n\n"
            "You are amending an existing set of challenge repos. "
            "Return ALL repos with their COMPLETE file sets — not just the changed ones. "
            "For repos you did not touch, copy their files exactly as-is."
        )
        parts.append(f"\n## Amendment Instructions\n{amend_instructions}")

    parts.append("\n## Challenges (complete scope)\n" if amend_instructions else "## Challenges to Generate\n")
    for i, desc in enumerate(challenge_descriptions, 1):
        parts.append(f"{i}. {desc}")

    if instructor_notes:
        parts.append(f"\n## Instructor Notes\n{instructor_notes}")

    if kb:
        parts.append(f"\n## Knowledge Base (reuse these patterns)\n{kb}")

    parts.append(f"\n## Reference Documentation\n{ref_docs}")

    if revision_feedback:
        parts.append(
            f"\n## Revision Required\nStudent agents reviewed your previous attempt and found issues. "
            f"Please fix them:\n\n{revision_feedback}"
        )

    if prior_files:
        label = (
            "## Existing Repos (preserve all content; return COMPLETE file sets for ALL repos)"
            if amend_instructions else
            "## Your Previous Output (for revision context)"
        )
        parts.append(f"\n{label}")
        for repo_name, files in prior_files.items():
            parts.append(f"\n### Repo: {repo_name}")
            parts.append(format_files_for_prompt(files))

    user_message = "\n".join(parts)

    raw = call_llm(
        system=BUILDER_SYSTEM_PROMPT,
        user=user_message,
        model=config.BUILDER_MODEL,
        max_tokens=config.BUILDER_MAX_TOKENS,
        agent="Builder",
    )

    data = parse_json_from_response(raw, context="Builder")

    if "repos" not in data:
        raise ValueError(
            f"Builder response missing 'repos' key.\n"
            f"Got keys: {list(data.keys())}\n"
            f"Response (first 500 chars): {raw[:500]}"
        )

    repos = []
    for r in data["repos"]:
        repos.append(
            ChallengeRepo(
                name=r["name"],
                description=r["description"],
                challenges=r["challenges"],
                install_command=r["install_command"],
                test_command=r["test_command"],
                files=r["files"],
            )
        )

    # Save challenge_type_notes to knowledge base if present
    notes = data.get("challenge_type_notes", "").strip()
    if notes and notes not in ("", "N/A", "None"):
        _save_challenge_type_notes(topic or challenge_descriptions[0], notes)

    return BuildResult(repos=repos)


def _save_challenge_type_notes(topic: str, notes: str) -> None:
    """Persist new challenge type knowledge to the knowledge base."""
    config.CHALLENGE_TYPES_DIR.mkdir(parents=True, exist_ok=True)
    slug = topic.lower().replace(" ", "_").replace("/", "_")[:40]
    dest = config.CHALLENGE_TYPES_DIR / f"{slug}.md"

    if dest.exists():
        # Append to existing
        existing = dest.read_text()
        dest.write_text(existing + f"\n\n---\n\n{notes}")
    else:
        dest.write_text(f"# Challenge Type: {topic}\n\n{notes}\n")


def write_repos(build_result: BuildResult, output_dir: Path) -> list[Path]:
    """Write all repos from a BuildResult to disk and git-init them."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_paths = []

    for repo in build_result.repos:
        repo_dir = output_dir / repo.name
        write_repo_files(repo_dir, repo.files)
        git_init(repo_dir)
        repo_paths.append(repo_dir)

    return repo_paths
