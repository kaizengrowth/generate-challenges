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


def _call_cli(system: str, user: str, model: str, max_tokens: int = 8096) -> str:
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
        ["claude", "--print", "--max-tokens", str(max_tokens)],
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
    original_raw = raw

    # Look for JSON content between markdown fences (```...```)
    # The response might have explanatory text before/after the fence
    if "```" in raw:
        # Find the first occurrence of opening fence
        first_fence = raw.find("```")
        # Find the first newline after the opening fence (language specifier may follow)
        after_fence = raw.find("\n", first_fence)
        if after_fence == -1:
            after_fence = first_fence + 3
        else:
            after_fence += 1

        # Find the closing fence
        closing_fence = raw.find("```", after_fence)
        if closing_fence != -1:
            # Extract content between fences
            raw = raw[after_fence:closing_fence]
        else:
            # No closing fence, try to extract from opening fence to end
            raw = raw[after_fence:]

    # Strip any leading/trailing whitespace
    raw = raw.strip()

    # Handle empty response
    if not raw:
        raise ValueError(
            f"{context} returned empty response after fence stripping.\n"
            f"Original response (first 500 chars):\n{original_raw[:500]}"
        )

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{context} returned invalid JSON.\n"
            f"Error: {e}\n"
            f"Response (first 500 chars):\n{raw[:500]}"
        ) from e
