"""
Orchestrator — coordinates the full challenge generation pipeline.

Flow:
  1. Builder generates challenge repos
  2. Expert Student evaluates each repo (white-box + black-box)
  3. Novice Student evaluates each repo (white-box + black-box)
  4. If issues found and iterations remaining: send feedback to Builder, repeat
  5. Save reference solutions and iteration log
"""

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from agents.builder import ChallengeRepo, BuildResult, build_challenges, write_repos
from agents.student_expert import ExpertFeedback, evaluate_repo as expert_evaluate, save_reference_solution
from agents.student_novice import NoviceFeedback, evaluate_repo as novice_evaluate
from tools.file_tools import read_repo_files
import config


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


def run_pipeline(
    challenge_descriptions: list[str],
    topic: str,
    output_dir: Path,
    instructor_notes: str = "",
    max_iterations: int = config.MAX_ITERATIONS,
    skip_novice: bool = False,
    skip_refine: bool = False,
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
        console: optional rich.Console for pretty-printed progress
    """
    def log(msg: str):
        if console:
            console.print(msg)
        else:
            print(msg)

    output_dir.mkdir(parents=True, exist_ok=True)
    ref_dir = output_dir / "reference_solutions"
    iteration_log = []

    result = RunResult(topic=topic, output_dir=output_dir)

    # ── Build initial challenge repos ────────────────────────────────────────
    log(f"\n[bold cyan]Building challenges...[/bold cyan]" if console else "\nBuilding challenges...")
    build_result = build_challenges(
        challenge_descriptions=challenge_descriptions,
        topic=topic,
        instructor_notes=instructor_notes,
    )

    if skip_refine:
        # Just write the repos and return
        repo_paths = write_repos(build_result, output_dir)
        log(f"Generated {len(repo_paths)} repo(s). Skipping student validation.")
        return result

    # ── Per-repo evaluation + refinement loop ────────────────────────────────
    for repo in build_result.repos:
        log(f"\n[bold]Repo: {repo.name}[/bold]" if console else f"\nRepo: {repo.name}")
        log(f"  Challenges: {', '.join(repo.challenges)}")

        prior_files: dict[str, str] | None = None
        expert_fb: ExpertFeedback | None = None
        novice_fb: NoviceFeedback | None = None
        repo_path: Path | None = None
        iteration = 0
        current_repo = repo
        current_build = BuildResult(repos=[repo])

        for iteration in range(1, max_iterations + 1):
            log(f"  Iteration {iteration}/{max_iterations}...")

            # Write repo to disk
            if repo_path and repo_path.exists():
                shutil.rmtree(repo_path)
            repo_paths = write_repos(current_build, output_dir)
            repo_path = repo_paths[0]

            # Expert student
            log("    Expert student evaluating...")
            expert_fb = expert_evaluate(current_repo, repo_path)
            log(f"    Tests passed: {expert_fb.tests_passed}")

            # Novice student
            if not skip_novice:
                log("    Novice student evaluating...")
                novice_fb = novice_evaluate(current_repo, repo_path, expert_fb.test_output)
                log(f"    Clarity score: {novice_fb.clarity_score}/5")
            else:
                novice_fb = NoviceFeedback(clarity_score=5, difficulty_assessment="appropriate")

            # Log this iteration
            iteration_log.append({
                "repo": current_repo.name,
                "iteration": iteration,
                "tests_passed": expert_fb.tests_passed,
                "expert_issues": expert_fb.technical_issues + expert_fb.test_quality_issues + expert_fb.infrastructure_issues,
                "novice_clarity": novice_fb.clarity_score,
                "novice_issues": novice_fb.confusion_points + novice_fb.missing_context,
            })

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
            log(f"    Issues found. Sending feedback to Builder...")

            current_build = build_challenges(
                challenge_descriptions=[current_repo.description],
                topic=topic,
                instructor_notes=instructor_notes,
                revision_feedback=feedback_summary,
                prior_files={current_repo.name: prior_files},
            )
            current_repo = current_build.repos[0]

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


def _update_lessons_learned(result: RunResult) -> None:
    """Append a summary of this run's lessons to lessons_learned.md."""
    lines = [f"\n## Run: {result.topic}\n"]
    for o in result.outcomes:
        if o.expert_feedback.has_issues or o.novice_feedback.has_issues:
            lines.append(f"### {o.repo.name} (resolved after {o.iterations} iteration(s))")
            for issue in o.expert_feedback.technical_issues:
                lines.append(f"- Technical: {issue}")
            for issue in o.novice_feedback.confusion_points:
                lines.append(f"- Clarity: {issue}")
    if len(lines) > 1:
        with open(config.LESSONS_LEARNED, "a") as f:
            f.write("\n".join(lines) + "\n")
