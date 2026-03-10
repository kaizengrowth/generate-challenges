"""
Unified LLM client — routes calls to either the Anthropic API or the Claude Code CLI.

Set USE_CLAUDE_CLI=true in .env to use your Claude Max/Pro subscription.
Set USE_CLAUDE_CLI=false (default) to use the API with ANTHROPIC_API_KEY.
"""

import os
import subprocess

import anthropic

import config


def call_llm(
    system: str,
    user: str,
    model: str,
    max_tokens: int,
) -> str:
    """
    Make a single LLM call and return the response text.

    Routes to the Anthropic API or Claude Code CLI based on config.USE_CLAUDE_CLI.
    """
    if config.USE_CLAUDE_CLI:
        return _call_cli(system=system, user=user, model=model)
    else:
        return _call_api(system=system, user=user, model=model, max_tokens=max_tokens)


def _call_api(system: str, user: str, model: str, max_tokens: int) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _call_cli(system: str, user: str, model: str) -> str:
    """
    Call the Claude Code CLI (`claude`) in print mode.

    The system prompt is prepended to the user message and piped via stdin.
    The --model flag is intentionally omitted: the CLI uses whatever model
    the user has configured in their Claude Code settings, which is correct
    for Max/Pro subscription users.

    Note: the prompt is passed via stdin (not as a positional argument) to
    avoid shell argument-length limits and quoting issues with long prompts.

    ANTHROPIC_API_KEY is stripped from the subprocess environment so the CLI
    uses its own OAuth/subscription credentials rather than any placeholder
    key that may be set in .env.
    """
    combined = f"<system>\n{system}\n</system>\n\n{user}"

    # Don't let a placeholder ANTHROPIC_API_KEY bleed into the CLI process
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    result = subprocess.run(
        ["claude", "--print"],
        input=combined,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )

    if result.returncode != 0:
        # The CLI sometimes writes errors to stdout rather than stderr
        error_detail = result.stderr or result.stdout or "(no output captured)"
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{error_detail}"
        )

    return result.stdout.strip()
