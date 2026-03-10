"""
Unified LLM client — routes calls to either the Anthropic API or the Claude Code CLI.

Set USE_CLAUDE_CLI=true in .env to use your Claude Max/Pro subscription.
Set USE_CLAUDE_CLI=false (default) to use the API with ANTHROPIC_API_KEY.
"""

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

    The system prompt is prepended to the user message since the CLI
    doesn't expose a separate system prompt flag in print mode.
    """
    combined = f"<system>\n{system}\n</system>\n\n{user}"

    result = subprocess.run(
        ["claude", "--print", "--model", model, combined],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{result.stderr}"
        )

    return result.stdout.strip()
