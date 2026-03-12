"""
Token usage tracker — accumulates LLM token counts across a run.

In API mode, input/output tokens come directly from response.usage.
In CLI mode, tokens are estimated from character counts (÷ 4) since the
Claude CLI does not expose usage metadata.
"""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class AgentTokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# Module-level state — reset between runs if needed
_usage: dict[str, AgentTokenUsage] = defaultdict(AgentTokenUsage)
_estimated: bool = False  # True when running in CLI mode (character-based estimates)


def record(agent: str, input_tokens: int, output_tokens: int) -> None:
    _usage[agent].input_tokens += input_tokens
    _usage[agent].output_tokens += output_tokens
    _usage[agent].calls += 1


def set_estimated(value: bool) -> None:
    global _estimated
    _estimated = value


def is_estimated() -> bool:
    return _estimated


def get_usage() -> dict[str, AgentTokenUsage]:
    return dict(_usage)


def reset() -> None:
    _usage.clear()
    global _estimated
    _estimated = False


def totals() -> AgentTokenUsage:
    result = AgentTokenUsage()
    for usage in _usage.values():
        result.input_tokens += usage.input_tokens
        result.output_tokens += usage.output_tokens
        result.calls += usage.calls
    return result
