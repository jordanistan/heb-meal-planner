"""Claude-backed generation. Optional: everything degrades gracefully when no
ANTHROPIC_API_KEY is set, so v1 runs fully without it.

Currently generates cooking steps for a recipe on demand. Steps are cached in
the DB by the caller so each recipe is generated once (LLM cost is per recipe,
not per request).
"""
from __future__ import annotations

import re

from ..config import settings


class LLMUnavailable(Exception):
    """Raised when a Claude call is requested but no API key is configured."""


def is_available() -> bool:
    return bool(settings.anthropic_api_key)


def generate_steps(name: str, ingredients: list[dict]) -> list[str]:
    """Return 4–8 concise cooking steps for a recipe. Requires an API key."""
    if not settings.anthropic_api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY is not set")

    import anthropic  # imported lazily so the app starts without the key

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    ing = ", ".join(f"{i['quantity']} {i['unit']} {i['name']}" for i in ingredients)
    prompt = (
        f'Write concise home-cook instructions for "{name}" using: {ing}. '
        "Return 4 to 8 short numbered steps, one per line, no preamble or notes."
    )
    msg = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in msg.content if getattr(block, "type", None) == "text"
    )
    steps = []
    for line in text.splitlines():
        line = re.sub(r"^\s*\d+[.)]\s*", "", line).strip()
        if line:
            steps.append(line)
    return steps[:8]
