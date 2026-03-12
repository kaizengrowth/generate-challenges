"""
Unified LLM client — routes calls to either the Anthropic API or the Claude Code CLI.

Set USE_CLAUDE_CLI=true in .env to use your Claude Max/Pro subscription.
Set USE_CLAUDE_CLI=false (default) to use the API with ANTHROPIC_API_KEY.
"""

import json
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
        return _call_cli(system=system, user=user, model=model, max_tokens=max_tokens)
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


def _call_cli(system: str, user: str, model: str, max_tokens: int = 0) -> str:  # max_tokens unused: CLI controls output length internally
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


def parse_json_from_response(raw: str, context: str = "") -> dict:
    """
    Parse JSON from an LLM response, handling common formatting issues.

    Args:
        raw: The raw LLM response
        context: Optional context string for error messages (e.g., "Builder response")

    Returns:
        Parsed JSON as a dict

    Raises:
        ValueError: If the response cannot be parsed as JSON
    """
    raw = raw.strip()

    # Fast path: try parsing as-is first (the happy path when model behaves)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Fallback: model wrapped JSON in a markdown fence despite instructions.
    # Only strip if the response starts with a fence — searching anywhere would
    # incorrectly match ``` inside file content (e.g., code blocks in a README).
    if raw.startswith("```"):
        # Skip the opening fence line (may have a language specifier like ```json)
        after_newline = raw.find("\n")
        if after_newline != -1:
            inner = raw[after_newline + 1:]
            # Strip trailing fence
            closing = inner.rfind("```")
            if closing != -1:
                inner = inner[:closing]
            raw = inner.strip()

    if not raw:
        raise ValueError(
            f"{context} returned an empty response.\n"
            f"Original response (first 500 chars):\n{raw[:500]}"
        )

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{context} returned invalid JSON.\n"
            f"Error: {e}\n"
            f"Response (first 500 chars):\n{raw[:500]}"
        ) from e
