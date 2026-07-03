"""
core/llm.py — thin Anthropic client wrapper shared by core/tailor.py.

Forces structured JSON output via tool-use (a single forced tool call) so
callers get validated dicts back instead of parsing free-form text.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


class LLMError(RuntimeError):
    """Raised when the Anthropic API can't be reached or returns something unusable."""


@lru_cache(maxsize=1)
def _client():
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file to use the real backend."
        )
    return Anthropic(api_key=api_key)


def structured_call(
    *,
    system: str,
    user: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, Any],
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Call Claude and force it to respond via a single tool call matching
    input_schema, so the result is always a validated dict — never prose to parse."""
    try:
        response = _client().messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=[{
                "name": tool_name,
                "description": tool_description,
                "input_schema": input_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
        )
    except LLMError:
        raise
    except Exception as e:  # anthropic.APIError and friends
        raise LLMError(f"Anthropic API call failed: {e}") from e

    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input

    raise LLMError("Model did not return the expected tool call.")
