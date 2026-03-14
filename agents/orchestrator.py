"""
Orchestrator — coordinates the full challenge generation pipeline.

Flow:
  1. Builder generates challenge repos
  2. Expert Student evaluates each repo (white-box + black-box)
  3. Novice Student evaluates each repo (white-box + black-box)
  4. If issues found and iterations remaining: send feedback to Builder, repeat
  5. Save reference solutions and iteration log
"""

import difflib
import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.builder import (
    ChallengeRepo, BuildResult, build_challenges, write_repos,
    plan_challenges, generate_repo, _save_challenge_type_notes,
)
from agents.student_expert import ExpertFeedback, evaluate_repo as expert_evaluate, save_reference_solution
from agents.student_novice import NoviceFeedback, evaluate_repo as novice_evaluate
from tools.file_tools import read_repo_files
from tools.llm_client import call_llm, parse_json_from_response
import config

MANIFEST_FILENAME = "build_manifest.json"


@dataclass
class RepoOutcome:
    repo: ChallengeRepo
    repo_path: Path
    expert_feedback: ExpertFeedback
    novice_feedback: NoviceFeedback
    iterations: int


@dataclass
class RunResult:
    topic: str
    output_dir: Path
    outcomes: list[RepoOutcome] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Topic: {self.topic}", f"Output: {self.output_dir}", ""]
        for o in self.outcomes:
            status = "PASSED" if o.expert_feedback.tests_passed else "FAILED"
            lines.append(f"  [{status}] {o.repo.name} (after {o.iterations} iteration(s))")
            if o.expert_feedback.has_issues:
                for issue in o.expert_feedback.technical_issues[:2]:
                    lines.append(f"    technical: {issue}")
            if o.novice_feedback.has_issues:
                lines.append(f"    clarity: {o.novice_feedback.clarity_score}/5")
        return "\n".join(lines)


def save_build_manifest(build_result: BuildResult, output_dir: Path, topic: str) -> Path:
    """
    Persist slim repo metadata (no file contents) to build_manifest.json.

    Written immediately after the initial build so the pipeline can be
    resumed with --resume-from without re-running the Builder.
    """
    manifest = {
        "topic": topic,
        "repos": [
            {
                "name": r.name,
                "description": r.description,
                "challenges": r.challenges,
                "install_command": r.install_command,
                "test_command": r.test_command,
                "ecosystem": r.ecosystem,
            }
            for r in build_result.repos
        ],
    }
    path = output_dir / MANIFEST_FILENAME
    output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
    return path


def load_build_manifest(resume_dir: Path) -> tuple[BuildResult, str]:
    """
    Reconstruct a BuildResult from a previously saved build_manifest.json.

    Returns (BuildResult, topic). The ChallengeRepo objects have empty
    ``files`` dicts because the actual files are already on disk.
    """
    path = resume_dir / MANIFEST_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"No {MANIFEST_FILENAME} found in {resume_dir}.\n"
            "Make sure this directory was created by this tool (--no-refine or a previous run)."
        )
    data = json.loads(path.read_text())
    repos = [
        ChallengeRepo(
            name=r["name"],
            description=r["description"],
            challenges=r["challenges"],
            install_command=r["install_command"],
            test_command=r["test_command"],
            files={},  # already on disk — read_repo_files() fetches them when needed
            ecosystem=r.get("ecosystem", ""),  # backward compat with old manifests
        )
        for r in data["repos"]
    ]
    return BuildResult(repos=repos), data["topic"]


def _summarize_changes(prior_files: dict[str, str], new_files: dict[str, str]) -> list[str]:
    """
    Use an LLM to produce a natural-language bullet list describing what the
    Builder changed between two iterations.
    """
    prior_keys = set(prior_files)
    new_keys = set(new_files)

    diff_sections = []

    for path in sorted(new_keys - prior_keys):
        diff_sections.append(f"### NEW FILE: {path}\n{new_files[path]}")

    for path in sorted(prior_keys - new_keys):
        diff_sections.append(f"### REMOVED FILE: {path}")

    for path in sorted(prior_keys & new_keys):
        old_lines = prior_files[path].splitlines(keepends=True)
        new_lines = new_files[path].splitlines(keepends=True)
        if old_lines == new_lines:
            continue
        diff = "".join(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}", n=3))
        if diff:
            diff_sections.append(f"### MODIFIED: {path}\n{diff}")

    if not diff_sections:
        return ["No changes detected"]

    diff_text = "\n\n".join(diff_sections)

    system = "You are analyzing changes a Builder agent made to a coding challenge repository between refinement iterations."
    user = f"""The Builder revised a coding challenge repo in response to student feedback. Below are the file changes (unified diff format; new files shown in full).

Summarize what was changed as a concise bulleted list. Each bullet should describe ONE meaningful change — what was fixed, added, or clarified and why it matters. Focus on intent and impact, not mechanics. Use present tense (e.g., "Adds test for...", "Fixes...", "Updates README to...").

{diff_text}

Return ONLY a JSON array of strings, one string per bullet. No markdown fences. Example: ["Adds a test asserting the button is disabled while a request is pending", "Fixes package.json to use vitest run so tests exit after one pass"]"""

    raw = call_llm(system=system, user=user, model=config.SUMMARIZE_CHANGES_MODEL, max_tokens=1000, agent="Change Summarizer")
    # The summarizer returns a JSON array directly
    try:
        data = parse_json_from_response(raw, context="Change summarizer")
        # Handle both array and object responses for backward compatibility
        if isinstance(data, list):
            return data
        return data.get("changes", [])
    except ValueError:
        # If parsing fails, return empty list rather than crashing
        return ["(changes could not be summarized)"]


def run_pipeline(
    challenge_descriptions: list[str],
    topic: str,
    output_dir: Path,
    instructor_notes: str = "",
    max_iterations: int = config.MAX_ITERATIONS,
    skip_novice: bool = False,
    skip_refine: bool = False,
    resume_from: Optional[Path] = None,
    initial_build: Optional["BuildResult"] = None,
    console=None,  # Optional rich Console for pretty output
) -> RunResult:
    """
    Run the full challenge generation pipeline.

    Args:
        challenge_descriptions: list of challenge descriptions to build
        topic: the broader topic (for knowledge base lookup and naming)
        output_dir: where to write repos and results
        instructor_notes: any guidance from the instructor
        max_iterations: how many refinement passes to allow
        skip_novice: if True, skip the novice student pass
        skip_refine: if True, generate only (no student validation or refinement)
        resume_from: if set, skip the Builder and load repos from this directory's
                     build_manifest.json (files already on disk)
        initial_build: if set, skip the Builder and use this BuildResult directly
                       (files not yet on disk — will be written on first iteration)
        console: optional rich.Console for pretty-printed progress
    """
    def log(msg: str, end: str = "\n"):
        if console:
            console.print(msg, end=end)
        else:
            print(msg, end=end, flush=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    ref_dir = output_dir / "reference_solutions"
    iteration_log = []

    # ── Build or resume ───────────────────────────────────────────────────────
    if resume_from:
        log(f"\n[bold cyan]Resuming from {resume_from}...[/bold cyan]" if console else f"\nResuming from {resume_from}...")
        build_result, topic = load_build_manifest(resume_from)
        output_dir = resume_from  # evaluate in the same dir
        ref_dir = output_dir / "reference_solutions"
    elif initial_build:
        log(f"\n[bold cyan]Using pre-built repos...[/bold cyan]" if console else "\nUsing pre-built repos...")
        build_result = initial_build
    else:
        # Phase 1: Plan (lightweight call to decide clustering + ecosystem)
        log(f"\n[bold cyan]Planning challenges...[/bold cyan]" if console else "\nPlanning challenges...", end="")
        _t = time.time()
        plan = plan_challenges(challenge_descriptions, topic, instructor_notes)
        log(f" done ({round(time.time() - _t)}s)")
        log(f"  {len(plan.repos)} repo(s) planned: {', '.join(r.name for r in plan.repos)}")

        # Phase 2: Generate each repo (filtered context, one at a time)
        repos = []
        for spec in plan.repos:
            log(f"\n[bold cyan]  Building repo: {spec.name}...[/bold cyan]" if console
                else f"\n  Building repo: {spec.name}...", end="")
            _t = time.time()
            repo = generate_repo(spec, topic, instructor_notes)
            log(f" done ({round(time.time() - _t)}s)")
            repos.append(repo)

        # Save challenge type notes to knowledge base
        notes = plan.challenge_type_notes.strip()
        if notes and notes not in ("", "N/A", "None"):
            _save_challenge_type_notes(topic or challenge_descriptions[0], notes)

        build_result = BuildResult(repos=repos)

    result = RunResult(topic=topic, output_dir=output_dir)

    if skip_refine and not resume_from:
        # Just write the repos and return
        repo_paths = write_repos(build_result, output_dir)
        save_build_manifest(build_result, output_dir, topic)
        log(f"Generated {len(repo_paths)} repo(s). Skipping student validation.")
        return result

    # Save manifest so this run can be resumed if interrupted
    if not resume_from:
        save_build_manifest(build_result, output_dir, topic)

    # ── Per-repo evaluation + refinement loop ────────────────────────────────
    for repo in build_result.repos:
        log(f"\n[bold]Repo: {repo.name}[/bold]" if console else f"\nRepo: {repo.name}")
        log(f"  Challenges: {', '.join(repo.challenges)}")

        expert_fb: ExpertFeedback | None = None
        novice_fb: NoviceFeedback | None = None
        iteration = 0
        current_repo = repo
        current_build = BuildResult(repos=[repo])
        pending_changes_summary: dict | None = None

        # On resume the files are already on disk; skip the first write
        repo_path: Path | None = (resume_from / repo.name) if resume_from else None
        skip_write_this_iteration = resume_from is not None

        for iteration in range(1, max_iterations + 1):
            log(f"  Iteration {iteration}/{max_iterations}...")

            # Write repo to disk (skipped on first iteration when resuming)
            if skip_write_this_iteration:
                skip_write_this_iteration = False
            else:
                if repo_path and repo_path.exists():
                    shutil.rmtree(repo_path)
                repo_paths = write_repos(current_build, output_dir)
                repo_path = repo_paths[0]

            # Run expert + novice in parallel (or just expert if --skip-novice)
            if not skip_novice:
                log("    Evaluating (expert + novice)...", end="")
                _t = time.time()
                with ThreadPoolExecutor(max_workers=2) as executor:
                    expert_future = executor.submit(expert_evaluate, current_repo, repo_path)
                    novice_future = executor.submit(novice_evaluate, current_repo, repo_path)
                    expert_fb = expert_future.result()
                    novice_fb = novice_future.result()
                log(f" done ({round(time.time() - _t)}s)")
            else:
                log("    Expert student evaluating...", end="")
                _t = time.time()
                expert_fb = expert_evaluate(current_repo, repo_path)
                log(f" done ({round(time.time() - _t)}s)")
                novice_fb = NoviceFeedback(clarity_score=5, difficulty_assessment="appropriate")
            log(f"    Tests passed: {expert_fb.tests_passed}")
            if not skip_novice:
                log(f"    Clarity score: {novice_fb.clarity_score}/5")

            # Log this iteration
            log_entry: dict = {
                "repo": current_repo.name,
                "iteration": iteration,
                "tests_passed": expert_fb.tests_passed,
                "expert_issues": expert_fb.technical_issues + expert_fb.test_quality_issues + expert_fb.infrastructure_issues,
                "novice_clarity": novice_fb.clarity_score,
                "novice_issues": novice_fb.confusion_points + novice_fb.missing_context,
            }
            if pending_changes_summary is not None:
                log_entry["changes_summary"] = pending_changes_summary
            iteration_log.append(log_entry)

            # Check if we're done
            no_issues = (
                expert_fb.tests_passed
                and not expert_fb.has_issues
                and not novice_fb.has_issues
            )
            if no_issues or iteration == max_iterations:
                break

            # Build feedback summary for next iteration
            feedback_parts = [expert_fb.to_feedback_text()]
            if novice_fb.has_issues:
                feedback_parts.append(novice_fb.to_feedback_text())
            feedback_summary = "\n\n".join(feedback_parts)

            prior_files = read_repo_files(repo_path)
            log(f"    Issues found. Rebuilding {current_repo.name}...", end="")
            _t = time.time()
            try:
                current_build = build_challenges(
                    challenge_descriptions=[current_repo.description],
                    topic=topic,
                    instructor_notes=instructor_notes,
                    revision_feedback=feedback_summary,
                    prior_files={current_repo.name: prior_files},
                )
                current_repo = current_build.repos[0]
            except (ValueError, KeyError) as e:
                log(f"\n    [yellow]Builder refinement failed: {e}[/yellow]" if console else f"\n    Warning: Builder refinement failed: {e}")
                log(f"    Keeping current build and skipping further refinement.")
                break
            log(f" done ({round(time.time() - _t)}s)")

            log(f"    Summarizing changes...", end="")
            _t = time.time()
            pending_changes_summary = _summarize_changes(prior_files, current_repo.files)
            log(f" done ({round(time.time() - _t)}s)")

        # Save reference solution
        if expert_fb and expert_fb.solution_files:
            save_reference_solution(expert_fb.solution_files, ref_dir, current_repo.name)
            log(f"    Reference solution saved to {ref_dir / current_repo.name}")

        result.outcomes.append(
            RepoOutcome(
                repo=current_repo,
                repo_path=repo_path,
                expert_feedback=expert_fb,
                novice_feedback=novice_fb,
                iterations=iteration,
            )
        )

    # Save iteration log
    log_path = output_dir / "iteration_log.json"
    log_path.write_text(json.dumps(iteration_log, indent=2))
    log(f"\nIteration log saved to {log_path}")

    # Update lessons_learned.md
    _update_lessons_learned(result)

    return result


def amend_pipeline(
    amend_dir: Path,
    new_challenge_descriptions: list[str],
    instructor_notes: str = "",
    max_iterations: int = config.MAX_ITERATIONS,
    skip_novice: bool = False,
    skip_refine: bool = False,
    console=None,
) -> RunResult:
    """
    Amend an existing output directory: add new challenges or modify existing ones.

    Loads the existing build manifest, reads current files from disk, calls the
    Builder with amendment context, then runs the full eval pipeline on the result.

    Args:
        amend_dir: path to an existing output directory (must contain build_manifest.json)
        new_challenge_descriptions: new challenge descriptions to add (can be empty if
                                    amending via instructor_notes alone)
        instructor_notes: instructions for modifying/extending existing challenges
        max_iterations: refinement loop limit
        skip_novice: skip novice student pass
        skip_refine: write amended repos only, skip all student evaluation
        console: optional rich.Console for pretty output
    """
    def log(msg: str, end: str = "\n"):
        if console:
            console.print(msg, end=end)
        else:
            print(msg, end=end, flush=True)

    # Load existing manifest and read files from disk
    build_result, topic = load_build_manifest(amend_dir)
    prior_files: dict[str, dict[str, str]] = {}
    for repo in build_result.repos:
        repo_path = amend_dir / repo.name
        if repo_path.is_dir():
            prior_files[repo.name] = read_repo_files(repo_path)

    # Build the amendment instruction for the Builder
    amend_parts: list[str] = []
    if new_challenge_descriptions:
        amend_parts.append(
            "Add the following new challenge(s) to the appropriate existing repo, "
            "or create a new repo if they don't fit the existing ones:"
        )
        for desc in new_challenge_descriptions:
            amend_parts.append(f"- {desc}")
    if instructor_notes:
        if amend_parts:
            amend_parts.append("")
        amend_parts.append(f"Additional instructions: {instructor_notes}")
    amend_instructions = "\n".join(amend_parts)

    # Full challenge scope = existing challenges + any new ones
    all_descriptions = [c for repo in build_result.repos for c in repo.challenges]
    all_descriptions.extend(new_challenge_descriptions)

    log(f"\n[bold cyan]Amending challenges in {amend_dir}...[/bold cyan]" if console else f"\nAmending challenges in {amend_dir}...", end="")
    _t = time.time()
    amended_build = build_challenges(
        challenge_descriptions=all_descriptions,
        topic=topic,
        instructor_notes=instructor_notes,
        amend_instructions=amend_instructions,
        prior_files=prior_files,
    )
    log(f" done ({round(time.time() - _t)}s)")

    return run_pipeline(
        challenge_descriptions=[],
        topic=topic,
        output_dir=amend_dir,
        instructor_notes=instructor_notes,
        max_iterations=max_iterations,
        skip_novice=skip_novice,
        skip_refine=skip_refine,
        initial_build=amended_build,
        console=console,
    )


def _update_lessons_learned(result: RunResult) -> None:
    """Append generalised lessons from this run to lessons_learned.md.

    Raw feedback items are sent through an LLM that strips challenge-specific
    details and extracts reusable principles, grouped by theme.
    """
    # Collect every raw issue from every outcome that needed refinement
    raw_issues: list[str] = []
    for o in result.outcomes:
        if o.expert_feedback.has_issues or o.novice_feedback.has_issues:
            for issue in o.expert_feedback.technical_issues:
                raw_issues.append(f"[Technical] {issue}")
            for issue in o.expert_feedback.test_quality_issues:
                raw_issues.append(f"[Test quality] {issue}")
            for issue in o.expert_feedback.infrastructure_issues:
                raw_issues.append(f"[Infrastructure] {issue}")
            for issue in o.novice_feedback.confusion_points:
                raw_issues.append(f"[Clarity] {issue}")
            for issue in o.novice_feedback.missing_context:
                raw_issues.append(f"[Missing context] {issue}")

    if not raw_issues:
        return

    issues_block = "\n".join(f"- {i}" for i in raw_issues)
    system = (
        "You are a curriculum-design expert. Your job is to distil raw feedback "
        "from student reviewers into reusable, general lessons for challenge authors. "
        "Output only plain Markdown — no preamble, no JSON, no code fences."
    )
    user = f"""The following issues were found while reviewing coding challenges on the topic "{result.topic}".

{issues_block}

Extract the general, reusable lessons that apply beyond these specific challenges. Follow these rules:
- Remove all references to specific challenge names, file names, variable names, or code snippets.
- Each lesson must be a principle that would apply to many challenges, not just the ones reviewed.
- Group related issues into a single lesson rather than listing each one separately.
- Where the issues cluster around a specific technology (e.g. React, TypeScript, REST APIs), you may scope the lesson to that technology — but keep it general within that scope.
- Write each lesson as one or two concrete, actionable sentences.
- Use a short `### Category` heading before each group (e.g. ### Hints and Guidance, ### Skeleton Files, ### Test Complexity, ### React).
- Omit any category that has no lessons.
- Do not repeat lessons already obvious from the category heading."""

    generalised = call_llm(
        system=system,
        user=user,
        model=config.SUMMARIZE_CHANGES_MODEL,
        max_tokens=1024,
        agent="Lessons Learned",
    )

    with open(config.LESSONS_LEARNED, "a") as f:
        f.write(f"\n## Run: {result.topic}\n\n")
        f.write(generalised.strip() + "\n")
