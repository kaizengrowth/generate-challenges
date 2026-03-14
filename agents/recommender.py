"""
Recommender Agent — suggests candidate challenges for a given topic.

The instructor reviews the suggestions and selects which ones to generate.
"""

import json
import time
from dataclasses import dataclass

import config
from tools.llm_client import call_llm, parse_json_from_response


@dataclass
class ChallengeCandidate:
    title: str
    description: str
    learning_objective: str
    difficulty: str  # "beginner" | "intermediate" | "advanced"
    challenge_type: str  # "implementation" | "debugging" | "ci_cd" | etc.


RECOMMENDER_SYSTEM_PROMPT = """You are a curriculum designer for a coding bootcamp. Given a topic,
suggest 5-10 coding challenges that would help students learn that topic effectively.

Good challenges:
- Have a clear, specific goal (not "learn React" but "build a component that...")
- Are testable (there is a right/wrong answer, or clear acceptance criteria)
- Build progressively in difficulty
- Cover different aspects of the topic
- Are realistic — similar to things students will encounter in real jobs

Challenge types to consider:
- implementation: student implements a class, function, component from scratch
- debugging: student is given broken code and must fix it
- ci_cd: student configures a CI/CD pipeline, Dockerfile, or workflow
- state_management: student manages application state with a specific library
- observability: student adds logging, metrics, or tracing to existing code
- architecture: student designs or refactors a system
- integration: student connects two systems or APIs together

Output ONLY a valid JSON object:
{
  "candidates": [
    {
      "title": "Click Counter",
      "description": "Build a React component with a button that increments a displayed count",
      "learning_objective": "Practice useState hook and event handling",
      "difficulty": "beginner",
      "challenge_type": "implementation"
    }
  ]
}

Rules:
- Suggest between 5 and 10 challenges
- Vary difficulty across beginner, intermediate, and advanced
- Make descriptions specific enough that a developer could build the challenge from just the description
- Output ONLY the JSON, no markdown fences
"""


def recommend_challenges(topic: str, extra_context: str = "") -> list[ChallengeCandidate]:
    """Ask the recommender agent to suggest challenges for a topic."""
    prompt = f"Topic: {topic}"
    if extra_context:
        prompt += f"\n\nAdditional context: {extra_context}"

    print("  Generating suggestions...", end="", flush=True)
    _t = time.time()
    raw = call_llm(
        system=RECOMMENDER_SYSTEM_PROMPT,
        user=prompt,
        model=config.RECOMMENDER_MODEL,
        max_tokens=config.RECOMMENDER_MAX_TOKENS,
        agent="Recommender",
    )
    print(f" done ({round(time.time() - _t)}s)")
    data = parse_json_from_response(raw, context="Recommender")
    return [
        ChallengeCandidate(
            title=c["title"],
            description=c["description"],
            learning_objective=c["learning_objective"],
            difficulty=c["difficulty"],
            challenge_type=c["challenge_type"],
        )
        for c in data["candidates"]
    ]
