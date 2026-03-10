#!/usr/bin/env python3
"""
Challenge Generation Platform — CLI entry point.

Usage:
  python main.py generate --topic "React state management"
  python main.py generate --topic "React state management" --no-refine
  python main.py generate --topic "React state management" --skip-novice
  python main.py generate --challenge "Build a click counter in React" --challenge "Build a toggle"
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
from agents.orchestrator import run_pipeline

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
):
    """Generate coding challenges from a topic or explicit challenge descriptions."""

    if not topic and not challenge:
        console.print("[red]Error: provide --topic or at least one --challenge[/red]")
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

    # ── Print summary ─────────────────────────────────────────────────────────
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
    console.print(f"\n[bold green]Done![/bold green] Challenge repos saved to: [cyan]{dest}[/cyan]")
    if (dest / "reference_solutions").exists():
        console.print(f"Reference solutions: [cyan]{dest / 'reference_solutions'}[/cyan]")


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
