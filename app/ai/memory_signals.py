"""
Memory signal gathering.

For each consent axis, two things:
  1. gather_<axis>_signals(user, db)   — pulls the raw data
     the AI should read for that axis.
  2. fingerprint_<axis>(signals)       — computes a short
     hash of that data. Comparing the current fingerprint
     to the one stored on user_memory tells us whether the
     axis has materially changed since the last regeneration.
     If unchanged, we skip the Claude call entirely.

Signals are returned as plain dicts (easy to serialise, easy
to hand to Claude, no ORM coupling downstream). The functions
here do NOT decide what to send Claude — they just pull data.
The generation orchestrator (Sitting 2) shapes and prompts.

Only the search axis has a size cap (last 25 queries). Owned
collections and wishlists are pulled in full — a real user's
collection is at most a few dozen items.
"""

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.collection import Collection, Wishlist
from app.models.fragrance import Fragrance
from app.models.note import FragranceNote
from app.models.search_query import SearchQuery
from app.models.user import User


# The search axis is capped so a rabbit-hole day doesn't
# dominate the taste signal (see design doc).
SEARCH_QUERY_LIMIT = 25


# --- Shared helpers ---------------------------------------
# Pulled out so each axis fingerprint stays a two-liner.

def _stable_hash(payload: str) -> str:
    """Short deterministic hash. Same input → same output, always."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _fragrance_context(fragrance: Optional[Fragrance]) -> dict:
    """
    Compact context for one fragrance: brand, name, family, and
    up to a handful of note names. This is what Claude sees per
    owned/wanted item. Kept lean — fuller context (descriptions,
    embeddings) is NOT sent, to keep the prompt small.
    """
    if fragrance is None:
        return {}
    family_name = (
        fragrance.scent_family.name
        if fragrance.scent_family else None
    )
    # Only official notes, capped, deduplicated by name.
    note_names: list[str] = []
    seen: set[str] = set()
    for fn in fragrance.fragrance_notes or []:
        if fn.note and fn.note.name and fn.note.name not in seen:
            note_names.append(fn.note.name)
            seen.add(fn.note.name)
            if len(note_names) >= 8:
                break
    return {
        "brand": fragrance.brand,
        "name": fragrance.name,
        "family": family_name,
        "notes": note_names,
    }


# --- Collection axis --------------------------------------
# Owned fragrances + ratings. This is the richest signal
# most users produce: what they chose to buy, what they
# think of it.

def gather_collection_signals(user: User, db: Session) -> list[dict]:
    """
    Return one dict per owned fragrance:
      {rating, date_added, fragrance: {brand, name, family, notes}}

    Uses joinedload so we don't do N+1 queries fetching
    each fragrance's family and notes separately.
    """
    items = (
        db.query(Collection)
        .filter(Collection.user_id == user.id)
        .options(
            joinedload(Collection.fragrance)
            .joinedload(Fragrance.scent_family),
            joinedload(Collection.fragrance)
            .joinedload(Fragrance.fragrance_notes)
            .joinedload(FragranceNote.note),
        )
        .all()
    )
    return [
        {
            "rating": item.personal_rating,
            "date_added": (
                item.date_added.isoformat()
                if item.date_added else None
            ),
            "fragrance": _fragrance_context(item.fragrance),
        }
        for item in items
    ]


def fingerprint_collection(signals: list[dict]) -> str:
    """
    Fingerprint of the collection axis.

    Uses only the fields that meaningfully affect what
    Claude would derive: fragrance identity + rating.
    Adding/removing an item changes the fingerprint;
    changing a rating changes it. Purchase price does not.
    """
    parts = sorted(
        f"{s['fragrance'].get('brand')}|{s['fragrance'].get('name')}|{s['rating']}"
        for s in signals
    )
    return _stable_hash("\n".join(parts))


# --- Wishlist axis ----------------------------------------
# Wanted fragrances + how urgently. Aspirational signal:
# what the user is drawn to, whether or not they've acted on it.

def gather_wishlist_signals(user: User, db: Session) -> list[dict]:
    """
    Return one dict per wishlisted fragrance:
      {priority, date_added, fragrance: {brand, name, family, notes}}
    """
    items = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user.id)
        .options(
            joinedload(Wishlist.fragrance)
            .joinedload(Fragrance.scent_family),
            joinedload(Wishlist.fragrance)
            .joinedload(Fragrance.fragrance_notes)
            .joinedload(FragranceNote.note),
        )
        .all()
    )
    return [
        {
            "priority": (
                item.priority.value if item.priority else None
            ),
            "date_added": (
                item.date_added.isoformat()
                if item.date_added else None
            ),
            "fragrance": _fragrance_context(item.fragrance),
        }
        for item in items
    ]


def fingerprint_wishlist(signals: list[dict]) -> str:
    """
    Wishlist fingerprint. Item identity + priority — the two
    things that determine what Claude would say.
    """
    parts = sorted(
        f"{s['fragrance'].get('brand')}|{s['fragrance'].get('name')}|{s['priority']}"
        for s in signals
    )
    return _stable_hash("\n".join(parts))


# --- Search axis ------------------------------------------
# Last 25 queries, most recent first. Deduplication and
# distinct-day weighting happen in the generation
# orchestrator; here we just pull rows honestly.

def gather_search_signals(user: User, db: Session) -> list[dict]:
    """
    Return one dict per search event, most recent first:
      {query, created_at}
    Capped at SEARCH_QUERY_LIMIT rows.
    """
    rows = (
        db.query(SearchQuery)
        .filter(SearchQuery.user_id == user.id)
        .order_by(SearchQuery.created_at.desc())
        .limit(SEARCH_QUERY_LIMIT)
        .all()
    )
    return [
        {
            "query": row.query,
            "created_at": (
                row.created_at.isoformat()
                if row.created_at else None
            ),
        }
        for row in rows
    ]


def fingerprint_search(signals: list[dict]) -> str:
    """
    Search fingerprint. Includes both the query text AND the
    calendar day it happened on, because the design weights
    queries by the number of distinct days they appear on —
    two searches on different days ≠ two searches same day.
    """
    parts = sorted(
        f"{s['query']}|{(s.get('created_at') or '')[:10]}"
        for s in signals
    )
    return _stable_hash("\n".join(parts))
