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
from tools import token_tracker


def call_llm(
    system: str,
    user: str,
    model: str,
    max_tokens: int,
    agent: str = "unknown",
) -> str:
    """
    Make a single LLM call and return the response text.

    Routes to the Anthropic API or Claude Code CLI based on config.USE_CLAUDE_CLI.
    Token usage is accumulated in tools.token_tracker keyed by `agent`.
    """
    if config.USE_CLAUDE_CLI:
        token_tracker.set_estimated(True)
        return _call_cli(system=system, user=user, model=model, max_tokens=max_tokens, agent=agent)
    else:
        return _call_api(system=system, user=user, model=model, max_tokens=max_tokens, agent=agent)


def _call_api(system: str, user: str, model: str, max_tokens: int, agent: str) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    token_tracker.record(
        agent=agent,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return response.content[0].text


def _call_cli(system: str, user: str, model: str, max_tokens: int = 0, agent: str = "unknown") -> str:  # max_tokens unused: CLI controls output length internally
    """
    Call the Claude Code CLI (`claude`) in print mode.

    The system prompt is passed via --system-prompt (not embedded in stdin) to
    prevent the model from treating <system> tags in the user message as prompt
    injection.  Only the user message is piped via stdin.

    --no-session-persistence avoids creating leftover session files for each
    agentic sub-call.

    The --model flag is intentionally omitted: the CLI uses whatever model the
    user has configured in their Claude Code settings (correct for Max/Pro users).

    ANTHROPIC_API_KEY is stripped from the subprocess environment so the CLI
    uses its own OAuth/subscription credentials rather than any placeholder key
    that may be set in .env.
    """
    # Strip vars that must not bleed into the subprocess:
    #   ANTHROPIC_API_KEY — placeholder keys cause auth errors
    #   CLAUDECODE        — its presence causes the CLI to refuse to start nested sessions
    _strip = {"ANTHROPIC_API_KEY", "CLAUDECODE"}
    env = {k: v for k, v in os.environ.items() if k not in _strip}

    result = subprocess.run(
        ["claude", "--print", "--no-session-persistence", "--output-format", "text", "--system-prompt", system],
        input=user,
        capture_output=True,
        text=True,
        timeout=config.CLI_TIMEOUT,
        env=env,
    )

    if result.returncode != 0:
        # The CLI sometimes writes errors to stdout rather than stderr
        error_detail = result.stderr or result.stdout or "(no output captured)"
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{error_detail}"
        )

    output = result.stdout.strip()

    # CLI doesn't expose usage metadata — estimate from character counts (÷4 ≈ tokens)
    token_tracker.record(
        agent=agent,
        input_tokens=(len(system) + len(user)) // 4,
        output_tokens=len(output) // 4,
    )

    return output


def parse_json_from_response(raw: str, context: str = "") -> dict:
    """
    Parse JSON from an LLM response, handling common formatting issues.

    Attempts in order:
    1. Parse as-is (happy path — model returned pure JSON)
    2. Extract from a markdown code fence anywhere in the response
       (handles preamble text + ```json ... ```)
    3. Slice from the first '{' onwards
       (handles short preamble like "Here is the JSON: {...}")

    Raises:
        ValueError: If the response cannot be parsed as JSON after all attempts
    """
    raw = raw.strip()

    if not raw:
        raise ValueError(f"{context} returned an empty response.")

    # 1. Fast path: try parsing as-is
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Markdown fence — search anywhere in the response (not just at start)
    fence_idx = raw.find("```")
    if fence_idx != -1:
        after_fence_line = raw.find("\n", fence_idx)
        if after_fence_line != -1:
            inner = raw[after_fence_line + 1:]
            closing = inner.rfind("```")
            if closing != -1:
                inner = inner[:closing]
            candidate = inner.strip()
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass

    # 3. Slice from first '{' — handles "Here is the result: {...}"
    brace_idx = raw.find("{")
    if brace_idx >= 0:
        try:
            return json.loads(raw[brace_idx:])
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"{context} returned invalid JSON.\n"
        f"Response (first 500 chars):\n{raw[:500]}"
    )
