#!/usr/bin/env python3
"""
Challenge Generation Platform — CLI entry point.

Usage:
  python main.py generate --topic "React state management"
  python main.py generate --topic "React state management" --no-refine
  python main.py generate --topic "React state management" --skip-novice
  python main.py generate --challenge "Build a click counter in React" --challenge "Build a toggle"
  python main.py generate --amend output/react-hooks --challenge "Add useCallback challenge"
  python main.py generate --amend output/react-hooks --notes "Make the stale closure challenge harder"
"""

import re
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

import config
from agents.recommender import recommend_challenges, ChallengeCandidate
from agents.orchestrator import run_pipeline, amend_pipeline, MANIFEST_FILENAME
from tools import token_tracker

app = typer.Typer(help="Generate coding challenges for bootcamp students.")
console = Console()


@app.command()
def generate(
    topic: Annotated[Optional[str], typer.Option("--topic", "-t", help="Topic to generate challenges for")] = None,
    challenge: Annotated[Optional[list[str]], typer.Option("--challenge", "-c", help="Challenge description (can repeat)")] = None,
    output_dir: Annotated[Optional[str], typer.Option("--output-dir", "-o", help="Output directory")] = None,
    max_iterations: Annotated[int, typer.Option("--max-iterations", help="Max refinement iterations")] = config.MAX_ITERATIONS,
    skip_novice: Annotated[bool, typer.Option("--skip-novice", help="Skip novice student evaluation (faster)")] = False,
    no_refine: Annotated[bool, typer.Option("--no-refine", help="Generate only, no student validation")] = False,
    notes: Annotated[Optional[str], typer.Option("--notes", "-n", help="Instructor notes for the builder")] = None,
    resume_from: Annotated[Optional[str], typer.Option("--resume-from", "-r", help="Resume evaluation from an existing output dir (skips Builder)")] = None,
    amend: Annotated[Optional[str], typer.Option("--amend", "-a", help="Add/extend challenges in an existing output dir")] = None,
):
    """Generate coding challenges from a topic or explicit challenge descriptions."""

    # ── Amend mode — add/extend challenges in an existing output dir ─────────
    if amend:
        if not challenge and not notes:
            console.print("[red]Error: --amend requires at least --challenge or --notes[/red]")
            raise typer.Exit(1)

        amend_path = Path(amend)
        if not (amend_path / MANIFEST_FILENAME).exists():
            console.print(f"[red]Error: no {MANIFEST_FILENAME} found in {amend_path}[/red]")
            console.print("Make sure this path was produced by a previous run of this tool.")
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Amending:[/bold] {amend_path}\n"
            f"[bold]New challenges:[/bold] {len(challenge) if challenge else 0}\n"
            f"[bold]Notes:[/bold] {notes or '(none)'}\n"
            f"[bold]Max iterations:[/bold] {max_iterations if not no_refine else 'N/A (--no-refine)'}",
            title="Challenge Amendment",
        ))

        result = amend_pipeline(
            amend_dir=amend_path,
            new_challenge_descriptions=list(challenge) if challenge else [],
            instructor_notes=notes or "",
            max_iterations=max_iterations,
            skip_novice=skip_novice,
            skip_refine=no_refine,
            console=console,
        )
        _print_results(result, amend_path)
        return

    # ── Resume mode — skip recommender + builder ─────────────────────────────
    if resume_from:
        resume_path = Path(resume_from)
        if not (resume_path / MANIFEST_FILENAME).exists():
            console.print(f"[red]Error: no {MANIFEST_FILENAME} found in {resume_path}[/red]")
            console.print("Make sure this path was produced by a previous run of this tool.")
            raise typer.Exit(1)

        console.print(Panel(
            f"[bold]Resuming from:[/bold] {resume_path}\n"
            f"[bold]Max iterations:[/bold] {max_iterations}",
            title="Resume Evaluation",
        ))

        result = run_pipeline(
            challenge_descriptions=[],   # unused when resume_from is set
            topic="",                    # loaded from manifest
            output_dir=resume_path,
            max_iterations=max_iterations,
            skip_novice=skip_novice,
            resume_from=resume_path,
            console=console,
        )
        _print_results(result, resume_path)
        return

    if not topic and not challenge:
        console.print("[red]Error: provide --topic, --challenge, --resume-from, or --amend[/red]")
        raise typer.Exit(1)

    # ── Determine challenge descriptions ────────────────────────────────────
    if challenge:
        # Explicit challenges provided — skip recommender
        descriptions = list(challenge)
        resolved_topic = topic or descriptions[0]
    else:
        # Topic provided — run recommender then let instructor select
        descriptions, resolved_topic = _recommender_flow(topic)
        if not descriptions:
            console.print("[yellow]No challenges selected. Exiting.[/yellow]")
            raise typer.Exit(0)

    # ── Resolve output directory ─────────────────────────────────────────────
    slug = re.sub(r"[^a-z0-9]+", "-", resolved_topic.lower()).strip("-")[:40]
    dest = Path(output_dir) if output_dir else config.OUTPUT_DIR / slug

    console.print(Panel(
        f"[bold]Topic:[/bold] {resolved_topic}\n"
        f"[bold]Challenges:[/bold] {len(descriptions)}\n"
        f"[bold]Output:[/bold] {dest}\n"
        f"[bold]Max iterations:[/bold] {max_iterations if not no_refine else 'N/A (--no-refine)'}",
        title="Challenge Generation",
    ))

    # ── Run pipeline ─────────────────────────────────────────────────────────
    result = run_pipeline(
        challenge_descriptions=descriptions,
        topic=resolved_topic,
        output_dir=dest,
        instructor_notes=notes or "",
        max_iterations=max_iterations,
        skip_novice=skip_novice,
        skip_refine=no_refine,
        console=console,
    )
    _print_results(result, dest)



def _print_results(result, dest: Path) -> None:
    """Print the results summary table."""
    console.print("\n")
    table = Table(title="Results", show_lines=True)
    table.add_column("Repo", style="cyan")
    table.add_column("Challenges")
    table.add_column("Tests", justify="center")
    table.add_column("Clarity", justify="center")
    table.add_column("Iterations", justify="center")

    for outcome in result.outcomes:
        tests = "[green]PASS[/green]" if outcome.expert_feedback.tests_passed else "[red]FAIL[/red]"
        clarity = f"{outcome.novice_feedback.clarity_score}/5"
        table.add_row(
            outcome.repo.name,
            "\n".join(outcome.repo.challenges),
            tests,
            clarity,
            str(outcome.iterations),
        )

    console.print(table)
    _print_token_report()
    console.print(f"\n[bold green]Done![/bold green] Challenge repos saved to: [cyan]{dest}[/cyan]")
    if (dest / "reference_solutions").exists():
        console.print(f"Reference solutions: [cyan]{dest / 'reference_solutions'}[/cyan]")


def _print_token_report() -> None:
    """Print a breakdown of token usage per agent."""
    usage = token_tracker.get_usage()
    if not usage:
        return

    estimated = token_tracker.is_estimated()
    label = "Tokens (est.)" if estimated else "Tokens"
    note = " [dim](estimated from character counts — CLI mode)[/dim]" if estimated else ""

    token_table = Table(title=f"Token Usage{note}", show_lines=True)
    token_table.add_column("Agent", style="cyan")
    token_table.add_column("Calls", justify="right")
    token_table.add_column(f"Input {label}", justify="right")
    token_table.add_column(f"Output {label}", justify="right")
    token_table.add_column(f"Total {label}", justify="right", style="bold")

    # Preferred display order
    order = ["Recommender", "Builder (Planner)", "Builder", "Expert Student", "Novice Student", "Change Summarizer", "Lessons Learned"]
    agents = [a for a in order if a in usage] + [a for a in usage if a not in order]

    for agent in agents:
        u = usage[agent]
        token_table.add_row(
            agent,
            str(u.calls),
            f"{u.input_tokens:,}",
            f"{u.output_tokens:,}",
            f"{u.total_tokens:,}",
        )

    totals = token_tracker.totals()
    token_table.add_row(
        "[bold]TOTAL[/bold]",
        str(totals.calls),
        f"[bold]{totals.input_tokens:,}[/bold]",
        f"[bold]{totals.output_tokens:,}[/bold]",
        f"[bold]{totals.total_tokens:,}[/bold]",
    )

    console.print("\n")
    console.print(token_table)


def _recommender_flow(topic: str) -> tuple[list[str], str]:
    """Run the recommender and let the instructor interactively select challenges."""
    console.print(f"\n[cyan]Getting challenge recommendations for:[/cyan] {topic}\n")

    candidates = recommend_challenges(topic)

    # Display candidates in a table
    table = Table(title=f"Suggested Challenges: {topic}", show_lines=True)
    table.add_column("#", justify="right", style="bold")
    table.add_column("Title", style="cyan")
    table.add_column("Description")
    table.add_column("Difficulty", justify="center")
    table.add_column("Type", justify="center")

    for i, c in enumerate(candidates, 1):
        diff_style = {"beginner": "green", "intermediate": "yellow", "advanced": "red"}.get(c.difficulty, "")
        table.add_row(
            str(i),
            c.title,
            c.description,
            f"[{diff_style}]{c.difficulty}[/{diff_style}]",
            c.challenge_type,
        )

    console.print(table)

    console.print("\n[bold]Select challenges to generate:[/bold]")
    console.print("  Enter numbers separated by commas (e.g. 1,3,5)")
    console.print("  Or press Enter to generate ALL")
    console.print("  Or type a description to add a custom challenge")

    raw = Prompt.ask("Selection", default="all")

    selected: list[ChallengeCandidate] = []

    if raw.lower() in ("", "all"):
        selected = candidates
    elif raw.isdigit() or "," in raw:
        # Parse numbers
        nums = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        selected = [candidates[n - 1] for n in nums if 1 <= n <= len(candidates)]
    else:
        # Treat as a custom description
        console.print(f"[yellow]Adding custom challenge:[/yellow] {raw}")
        from agents.recommender import ChallengeCandidate
        selected = [ChallengeCandidate(
            title=raw,
            description=raw,
            learning_objective="",
            difficulty="intermediate",
            challenge_type="implementation",
        )]

    if not selected:
        return [], topic

    # Allow instructor to add notes
    notes_prompt = Prompt.ask("\nAny notes or special requirements for the builder? (Enter to skip)", default="")

    descriptions = [f"{c.title}: {c.description}" for c in selected]
    return descriptions, topic


if __name__ == "__main__":
    app()
