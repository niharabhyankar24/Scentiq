"""
Standardized Claude API client.

Every Claude call in the app should go through this module.
Purposes:

  1. Uniform error handling. Callers get a Result object,
     not exceptions. Failures are categorised so callers
     can choose how to degrade (fall back to cached data,
     return default, retry, etc).

  2. Consistent logging. Every failure is logged with a
     [CLAUDE] prefix and a call_site tag so you can grep
     Railway logs to see which feature had which failures.

  3. Single place to add cross-cutting concerns later —
     retries, caching, cost tracking, model swaps. Adding
     these here means every caller benefits without a
     rewrite each.

The helper does NOT retry failed calls. Retries are context-
dependent (idempotency, backoff, cost implications) and
better handled by callers who understand their situation.
Fail fast, let the caller decide.

Usage:

    result = call_claude(
        system_prompt="You are a helpful assistant.",
        user_content="Hello.",
        call_site="memory:collection",
        expect_json=True,
    )
    if result.success:
        parsed = result.data           # dict when expect_json=True
    else:
        # result.failure_reason tells you what went wrong
        # (an enum value). result.error_message has detail.
        pass
"""

import os
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from anthropic import Anthropic


# --- Configuration ----------------------------------------
# Defaults sensible for the current app. All can be overridden
# per-call. Environment variable lets ops-level model swaps
# happen without a code deploy.

DEFAULT_MODEL = os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-5")
DEFAULT_MAX_TOKENS = 1000


# --- Failure taxonomy -------------------------------------
# Every possible failure gets categorised. Adding new
# categories is a non-breaking change — existing callers
# who only check `success` are unaffected.

class FailureReason(str, Enum):
    NETWORK_ERROR = "network_error"       # timeout, connection refused, etc.
    API_ERROR = "api_error"               # auth, rate limit, credits, 5xx
    EMPTY_RESPONSE = "empty_response"     # Claude returned no content
    PARSE_ERROR = "parse_error"           # asked for JSON, got non-JSON
    SHAPE_ERROR = "shape_error"           # JSON parsed but wrong structure
    UNKNOWN = "unknown"                   # catch-all, should be rare


# --- Result object ----------------------------------------
# Callers inspect `success` first. If True, `data` holds the
# response (dict if expect_json, str otherwise). If False,
# `failure_reason` and `error_message` describe the failure.
#
# Using a dataclass over a tuple makes it obvious at call
# sites what each field means, and adding fields later
# (e.g. token counts, latency) is a non-breaking change.

@dataclass
class Result:
    success: bool
    data: Any = None
    failure_reason: Optional[FailureReason] = None
    error_message: Optional[str] = None
    # Room for future additions without breaking callers:
    metadata: dict = field(default_factory=dict)


# --- Helpers ----------------------------------------------

def _log_failure(
    call_site: str,
    reason: FailureReason,
    message: str
) -> None:
    """
    Consistent failure log line. `flush=True` so the message
    appears immediately in Railway logs, not buffered.
    """
    print(
        f"[CLAUDE] {call_site} failed ({reason.value}): {message}",
        flush=True,
    )


def _extract_text(response) -> Optional[str]:
    """
    Pull the plain text out of an Anthropic response. Returns
    None if the response has no text content (rare but possible).
    """
    if not response.content:
        return None
    for block in response.content:
        # Anthropic can return multiple block types; we only
        # care about text blocks here. If future features use
        # tool_use or other block types, extend this.
        if getattr(block, "type", None) == "text":
            text = getattr(block, "text", "").strip()
            if text:
                return text
    return None


def _strip_code_fences(raw: str) -> str:
    """
    Claude sometimes wraps JSON in ```json ... ``` even when
    told not to. Strip those defensively.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


# --- Main entry point -------------------------------------

def call_claude(
    system_prompt: str,
    user_content: str,
    call_site: str,
    expect_json: bool = False,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
) -> Result:
    """
    Make a single call to Claude with standardized error handling.

    Args:
      system_prompt: Instructions to the model.
      user_content: The user-facing prompt payload.
      call_site: Identifier for logs, e.g. "memory:collection".
                 Not sent to Claude — internal only.
      expect_json: If True, response is parsed as JSON. Failures
                   in parsing become PARSE_ERROR results.
      model: Override the default model.
      max_tokens: Override the default token cap.

    Returns:
      Result. Always inspect `.success` before using `.data`.
    """
    active_model = model or DEFAULT_MODEL
    active_max_tokens = max_tokens or DEFAULT_MAX_TOKENS

    # --- Make the API call ---
    # Network and API errors happen here. Everything else is
    # a response we received but couldn't use.
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=active_model,
            max_tokens=active_max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception as e:
        # Anthropic SDK raises subclass exceptions for various
        # errors. Rather than importing and matching every one,
        # we categorise by message inspection. This is
        # deliberately loose — future SDK versions may change
        # exception hierarchies, but the string patterns are
        # more stable.
        message = str(e)
        lower = message.lower()
        if any(term in lower for term in [
            "timeout", "connection", "network", "unreachable"
        ]):
            reason = FailureReason.NETWORK_ERROR
        elif any(term in lower for term in [
            "unauthorized", "authentication", "api key",
            "rate limit", "quota", "credit", "billing",
            "overloaded", "500", "502", "503",
        ]):
            reason = FailureReason.API_ERROR
        else:
            reason = FailureReason.UNKNOWN
        _log_failure(call_site, reason, message)
        return Result(
            success=False,
            failure_reason=reason,
            error_message=message,
        )

    # --- Extract text ---
    raw_text = _extract_text(response)
    if raw_text is None:
        _log_failure(
            call_site,
            FailureReason.EMPTY_RESPONSE,
            "Claude returned no text content",
        )
        return Result(
            success=False,
            failure_reason=FailureReason.EMPTY_RESPONSE,
            error_message="No text content in response",
        )

    # --- Return early for plain-text callers ---
    if not expect_json:
        return Result(success=True, data=raw_text)

    # --- Parse JSON ---
    cleaned = _strip_code_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        _log_failure(
            call_site,
            FailureReason.PARSE_ERROR,
            f"JSON decode failed: {e}",
        )
        return Result(
            success=False,
            failure_reason=FailureReason.PARSE_ERROR,
            error_message=f"Invalid JSON: {e}",
        )

    return Result(success=True, data=parsed)