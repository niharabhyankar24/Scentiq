"""
Memory generator.

The heart of the memory feature. Given a user, this module:

  1. Loads (or creates) their user_memory row.
  2. For each of the three consent axes:
     - If the user has NOT opted in, clears the axis on the row.
     - If they have, gathers signals and computes a fingerprint.
       Compares against the fingerprint stored on the row.
       If unchanged, skips regeneration (money saved, no
       Claude call). If changed, runs the axis through a
       pre-computation step, calls Claude, parses the JSON,
       filters out de-ranked tags, and stores.
  3. Returns a MemoryResponse-shaped dict.

Design decisions and their rationale live inline near the
code they govern. Section markers keep concerns separated.
"""

import os
import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional
import secrets

from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_memory import UserMemory

from app.ai.memory_signals import (
    gather_collection_signals,
    gather_wishlist_signals,
    gather_search_signals,
    fingerprint_collection,
    fingerprint_wishlist,
    fingerprint_search,
)

load_dotenv()


# --- Configuration ----------------------------------------
# Model name is a config value, not a hardcoded string, so
# swapping models later (Haiku, Opus, or a future release)
# is a one-line change. Environment override lets us test
# different models without a code push.
DEFAULT_MODEL = "claude-sonnet-4-5"
CLAUDE_MODEL = os.getenv("MEMORY_CLAUDE_MODEL", DEFAULT_MODEL)

# Sonnet is verbose by default. Cap at 800 tokens per axis
# — enough for a 4-sentence paragraph and 6-8 observations,
# not enough to ramble. Zero-downside cost saver.
MAX_TOKENS_PER_AXIS = 800

# De-rank threshold from the design: two deletes of the
# same tag on the same axis triggers permanent de-rank
# on that axis. This constant is the enforcement threshold.
DERANK_THRESHOLD = 2


# --- Rate-limit guard -------------------------------------
# In-memory per-user counter to protect against runaway
# regeneration (bug loops, malicious retries). Not
# restart-safe by design — a restart resets counters,
# which is fine at single-instance Railway scale.
#
# If we ever go multi-instance, migrate this to Redis or
# a database column. Sitting-1 note lives here so future
# me knows why the counter exists.

_REGEN_WINDOW_SECONDS = 3600         # one-hour window
_REGEN_LIMIT_PER_WINDOW = 20         # ~1 every 3 min max
_regen_log: dict[int, list[float]] = defaultdict(list)


def _within_rate_limit(user_id: int) -> bool:
    """
    Return True if this user has NOT exceeded the regen
    ceiling in the current sliding window. Also prunes
    stale entries so the dict doesn't grow forever.
    """
    now = time.time()
    cutoff = now - _REGEN_WINDOW_SECONDS
    recent = [t for t in _regen_log[user_id] if t > cutoff]
    _regen_log[user_id] = recent

    if len(recent) >= _REGEN_LIMIT_PER_WINDOW:
        return False

    _regen_log[user_id].append(now)
    return True


# --- Pre-computation --------------------------------------
# For each axis, we compute a small structured summary of
# the signals BEFORE handing them to Claude. Two reasons:
# (a) the computed facts stay consistent across
# regenerations regardless of prose variation, and (b) it
# frees Claude's attention to spend on insight rather than
# arithmetic.

def _precompute_collection(signals: list[dict]) -> dict:
    """Structured summary of the collection axis."""
    if not signals:
        return {}

    rated = [s for s in signals if s.get("rating") is not None]
    top_rated = sorted(
        rated, key=lambda s: s["rating"], reverse=True
    )[:5]
    low_rated = [s for s in rated if s["rating"] <= 4]

    family_counts: Counter = Counter()
    ratings_by_family: dict[str, list[int]] = defaultdict(list)
    for s in signals:
        fam = s["fragrance"].get("family")
        if fam:
            family_counts[fam] += 1
            if s.get("rating") is not None:
                ratings_by_family[fam].append(s["rating"])

    family_avg = {
        fam: round(sum(vals) / len(vals), 1)
        for fam, vals in ratings_by_family.items()
        if vals
    }

    return {
        "total_owned": len(signals),
        "top_rated": [
            {
                "label": f"{s['fragrance']['brand']} "
                         f"{s['fragrance']['name']}",
                "rating": s["rating"],
                "family": s["fragrance"].get("family"),
            }
            for s in top_rated
        ],
        "low_rated": [
            {
                "label": f"{s['fragrance']['brand']} "
                         f"{s['fragrance']['name']}",
                "rating": s["rating"],
                "family": s["fragrance"].get("family"),
            }
            for s in low_rated
        ],
        "family_distribution": dict(family_counts),
        "avg_rating_by_family": family_avg,
    }


def _precompute_wishlist(signals: list[dict]) -> dict:
    """Structured summary of the wishlist axis."""
    if not signals:
        return {}

    priority_counts: Counter = Counter()
    family_counts: Counter = Counter()
    for s in signals:
        if s.get("priority"):
            priority_counts[s["priority"]] += 1
        fam = s["fragrance"].get("family")
        if fam:
            family_counts[fam] += 1

    return {
        "total_wanted": len(signals),
        "priority_distribution": dict(priority_counts),
        "family_distribution": dict(family_counts),
        "high_priority_items": [
            {
                "label": f"{s['fragrance']['brand']} "
                         f"{s['fragrance']['name']}",
                "family": s["fragrance"].get("family"),
            }
            for s in signals if s.get("priority") == "high"
        ],
    }


def _precompute_search(signals: list[dict]) -> dict:
    """
    Structured summary of the search axis.

    Implements the design's "distinct-day" weighting:
    a query searched on more different days weighs more
    than one searched many times on one day.
    """
    if not signals:
        return {}

    days_per_query: dict[str, set[str]] = defaultdict(set)
    for s in signals:
        q = s.get("query", "").strip()
        day = (s.get("created_at") or "")[:10]
        if q and day:
            days_per_query[q].add(day)

    # Sort queries by number of distinct days, descending.
    ranked = sorted(
        (
            {"query": q, "distinct_days": len(days)}
            for q, days in days_per_query.items()
        ),
        key=lambda x: x["distinct_days"],
        reverse=True
    )

    return {
        "total_searches": len(signals),
        "unique_queries": len(days_per_query),
        "queries_by_persistence": ranked[:15],
    }


# --- System prompts ---------------------------------------
# One prompt per axis, tuned for the pre-computed context
# each receives. All three share a JSON-only output rule
# and a de-rank instruction. Kept as module constants for
# clarity and for future prompt-caching (they're static).

_COLLECTION_SYSTEM_PROMPT = """
You are a fragrance taste analyst reading a user's owned
collection. You will receive raw fragrance data plus a
pre-computed summary of top-rated items, low-rated items,
and family distributions. Trust the summary as ground
truth for those numbers. Your job is to notice PATTERNS
and form HYPOTHESES about the user's taste that the raw
numbers alone don't state.

Good observations connect data points. Bad observations
restate them. Aim for the good kind.

Rules:
- Ground every claim in the data provided. Never invent
  fragrances, notes, or ratings.
- Prefer specific over generic. "Your two 9-rated items
  share an unusual central note" beats "you like woody
  scents."
- If the data is thin, say so directly. Don't stretch.
- Avoid marketing language: no "sophisticated,"
  "captivating," "signature." Real language only.
- Each observation must have a tag drawn from notes,
  families, brands, or characteristics visible in the
  data. Prefer the vocabulary you see in the input.
- If a list of de-ranked tags is provided, do not produce
  any observation whose tag matches one of them.

Output format — return ONLY raw JSON, no markdown fences,
no preamble:
{
  "paragraph": "3-5 sentences of grounded prose.",
  "observations": [
    {"text": "specific observation", "tag": "tag_here"},
    ...
  ]
}
"""

_WISHLIST_SYSTEM_PROMPT = """
You are a fragrance taste analyst reading a user's wishlist —
the fragrances they've said they want. This is aspirational
data: what they're drawn to, whether or not they've bought it.

You will receive raw wishlist data plus a pre-computed
summary of priorities and families.

Wishlists reveal different signals than collections. Look for:
- Style drift (is the user reaching toward something new?)
- Focused vs scattered interest
- Alignment or divergence between what they want and their
  stated urgency (priority)

Same rules as always:
- Ground every claim. Never invent.
- Specific over generic.
- Real language. No marketing.
- Each observation gets a tag from the visible vocabulary.
- Skip any observation whose tag matches the de-ranked list.

Output format — return ONLY raw JSON:
{
  "paragraph": "3-5 sentences.",
  "observations": [
    {"text": "specific observation", "tag": "tag"},
    ...
  ]
}
"""

_SEARCH_SYSTEM_PROMPT = """
You are a fragrance taste analyst reading a user's search
history. This is curiosity data: what they wanted to know
about, whether or not they bought or wishlisted it.

The pre-computed summary ranks queries by how many DIFFERENT
DAYS the user searched them. A query searched on 5 different
days is a stronger signal than one searched 10 times on one
day (that's a rabbit hole, not a durable interest).

Focus your observations on:
- Persistent interests (queries with many distinct days)
- Themes across queries (do multiple queries suggest one
  underlying interest?)
- Curiosity that hasn't yet shown up in the collection

Rules:
- Ground every claim in the data.
- Specific over generic.
- No marketing language.
- Tag each observation from visible vocabulary.
- Skip de-ranked tags.

Output format — return ONLY raw JSON:
{
  "paragraph": "3-5 sentences.",
  "observations": [
    {"text": "specific observation", "tag": "tag"},
    ...
  ]
}
"""


# --- Claude call ------------------------------------------
# Isolated so per-axis logic doesn't have to worry about
# API mechanics. Returns parsed dict or None on failure.
# Failure never propagates — the caller keeps the stored
# axis on failure and moves on.

def _call_claude_for_axis(
    system_prompt: str,
    axis_name: str,
    signals: list[dict],
    precomputed: dict,
    deranked_tags: list[str],
) -> Optional[dict]:
    """
    Call Claude for one axis. Returns parsed JSON with
    keys 'paragraph' and 'observations', or None on any
    error (API failure, malformed response, empty output).
    """
    user_payload = {
        "axis": axis_name,
        "precomputed_summary": precomputed,
        "raw_signals": signals,
        "deranked_tags": deranked_tags,
    }
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS_PER_AXIS,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            }],
        )
        raw = response.content[0].text.strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)

        # Minimum viable shape check. If Claude returned
        # something structurally wrong, treat as failure.
        if not isinstance(parsed, dict):
            return None
        if "paragraph" not in parsed or "observations" not in parsed:
            return None
        if not isinstance(parsed["observations"], list):
            return None
        return parsed
    except Exception as e:
        print(
            f"[MEMORY GEN] Claude call failed for {axis_name}: {e}",
            flush=True
        )
        return None


# --- De-rank enforcement ----------------------------------
# The system prompt tells Claude to skip de-ranked tags,
# but we trust-but-verify. Any observation Claude returns
# with a de-ranked tag is stripped before storage. This
# also renumbers ids to stay sequential.

def _apply_derank_filter(
    observations: list[dict],
    deranked_tags: set[str],
) -> list[dict]:
    """Drop observations with de-ranked tags. Renumber ids."""
    cleaned = []
    for obs in observations:
        if not isinstance(obs, dict):
            continue
        tag = obs.get("tag", "").strip()
        text = obs.get("text", "").strip()
        if not text:
            continue
        if tag in deranked_tags:
            continue
        cleaned.append({"text": text, "tag": tag})
    # Assign short random ids AFTER filtering. Ids are
    # internal identifiers — the frontend displays list
    # position as the visible number, not the id itself.
    # Random ids avoid renumbering races on delete.
    return [
        {"id": f"o_{secrets.token_hex(3)}", "text": o["text"], "tag": o["tag"]}
        for o in cleaned
    ]


# --- Per-axis orchestration -------------------------------
# One helper per axis so the main loop stays readable.
# Each returns True if the axis was actually regenerated,
# False if skipped (unchanged fingerprint or consent off).

def _get_or_create_memory_row(user: User, db: Session) -> UserMemory:
    """
    Fetch this user's memory row, creating a fresh one if
    they've never had one. Lazy creation avoids a row per
    user until they actually opt into something.
    """
    row = db.query(UserMemory).filter(
        UserMemory.user_id == user.id
    ).first()
    if row:
        return row
    row = UserMemory(user_id=user.id)
    db.add(row)
    db.flush()   # get an id without committing yet
    return row


def _clear_axis(memory_row: UserMemory, axis: str) -> None:
    """
    Wipe an axis when consent has been revoked. Paragraph,
    observations, timestamp, fingerprint, and derank
    counters all reset. The row itself stays because other
    axes may still be in use.
    """
    setattr(memory_row, f"{axis}_paragraph", None)
    setattr(memory_row, f"{axis}_observations", [])
    setattr(memory_row, f"{axis}_last_updated", None)
    setattr(memory_row, f"{axis}_derank_counters", {})
    # Fingerprint column will exist after the migration for
    # it lands; for now, we set it via setattr and let the
    # ORM handle absence gracefully.
    try:
        setattr(memory_row, f"{axis}_fingerprint", None)
    except Exception:
        pass


def _regenerate_axis(
    axis: str,
    signals: list[dict],
    current_fingerprint: str,
    memory_row: UserMemory,
    system_prompt: str,
    precomputed: dict,
) -> bool:
    """
    Regenerate ONE axis if its fingerprint has changed.
    Returns True if a Claude call was made, False if skipped.
    """
    stored_fingerprint = getattr(
        memory_row, f"{axis}_fingerprint", None
    )
    if stored_fingerprint == current_fingerprint:
        return False   # nothing changed, keep stored memory

    # Read de-rank counters and derive the "banned" tags.
    counters = getattr(memory_row, f"{axis}_derank_counters", {}) or {}
    deranked_tags = {
        tag for tag, count in counters.items()
        if count >= DERANK_THRESHOLD
    }

    parsed = _call_claude_for_axis(
        system_prompt=system_prompt,
        axis_name=axis,
        signals=signals,
        precomputed=precomputed,
        deranked_tags=sorted(deranked_tags),
    )
    if parsed is None:
        # Failure. Keep whatever's already stored for this
        # axis, don't touch the fingerprint. Next call
        # tries again.
        return False

    cleaned_observations = _apply_derank_filter(
        parsed.get("observations", []),
        deranked_tags,
    )

    setattr(memory_row, f"{axis}_paragraph", parsed["paragraph"])
    setattr(memory_row, f"{axis}_observations", cleaned_observations)
    setattr(memory_row, f"{axis}_last_updated", datetime.utcnow())
    setattr(memory_row, f"{axis}_fingerprint", current_fingerprint)
    return True


# --- Main entry point -------------------------------------
# The single function the endpoint will call. Does
# everything: fetches row, checks each axis, calls Claude
# where needed, updates row, returns response shape.

def regenerate_memory(user: User, db: Session) -> dict:
    """
    Bring a user's memory up to date and return the shape
    the endpoint hands back to the frontend.

    Behaviour:
      - Consent OFF for an axis: axis is cleared, returns None.
      - Consent ON, fingerprint unchanged: no Claude call,
        returns stored content.
      - Consent ON, fingerprint changed: Claude call, store,
        return fresh content.
      - Rate-limit exceeded: no Claude calls at all, returns
        whatever is currently stored. User gets last-known
        memory instead of an error.
    """
    memory_row = _get_or_create_memory_row(user, db)
    rate_limit_ok = _within_rate_limit(user.id)

    # Each axis: (name, consent_flag, gather_fn, fingerprint_fn,
    #             precompute_fn, system_prompt)
    axes = [
        (
            "collection",
            user.consent_collection,
            gather_collection_signals,
            fingerprint_collection,
            _precompute_collection,
            _COLLECTION_SYSTEM_PROMPT,
        ),
        (
            "wishlist",
            user.consent_wishlist,
            gather_wishlist_signals,
            fingerprint_wishlist,
            _precompute_wishlist,
            _WISHLIST_SYSTEM_PROMPT,
        ),
        (
            "search",
            user.consent_search_history,
            gather_search_signals,
            fingerprint_search,
            _precompute_search,
            _SEARCH_SYSTEM_PROMPT,
        ),
    ]

    for name, consented, gather, fingerprint_fn, precompute, prompt in axes:
        if not consented:
            _clear_axis(memory_row, name)
            continue

        signals = gather(user, db)
        current_fp = fingerprint_fn(signals)
        precomputed = precompute(signals)

        if not rate_limit_ok:
            # Rate limited — do not attempt regeneration.
            # Keep whatever is stored for this axis.
            continue

        _regenerate_axis(
            axis=name,
            signals=signals,
            current_fingerprint=current_fp,
            memory_row=memory_row,
            system_prompt=prompt,
            precomputed=precomputed,
        )

    db.commit()
    db.refresh(memory_row)

    return _to_response_shape(memory_row, user)


# --- Response shaping -------------------------------------
# Reads the memory_row and returns a dict matching
# MemoryResponse. Axes the user hasn't consented to appear
# as None so the frontend can skip rendering them.

def _to_response_shape(memory_row: UserMemory, user: User) -> dict:
    """Shape the row into the response the endpoint returns."""

    def axis_block(axis: str, consented: bool) -> Optional[dict]:
        if not consented:
            return None
        paragraph = getattr(memory_row, f"{axis}_paragraph")
        if paragraph is None:
            return None
        return {
            "paragraph": paragraph,
            "observations": getattr(
                memory_row, f"{axis}_observations", []
            ) or [],
            "last_updated": getattr(
                memory_row, f"{axis}_last_updated"
            ),
        }

    return {
        "collection": axis_block("collection", user.consent_collection),
        "wishlist": axis_block("wishlist", user.consent_wishlist),
        "search": axis_block("search", user.consent_search_history),
    }
