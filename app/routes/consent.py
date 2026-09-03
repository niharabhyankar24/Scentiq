"""
Consent routes.

Two endpoints for reading and updating a user's three
consent booleans.

Honesty guarantee enforced here ("off means gone"): after any
PUT, every axis whose outgoing state is OFF has BOTH its raw
inputs and its AI-derived memory purged, in the same
transaction as the flag flip. This is state-based, not
transition-based: if the outgoing state is "off", we guarantee
no stored data exists for that axis, regardless of how it got
there, and regardless of whether the user ever revisits the
Signature page.

Per axis, "off" purges:
  search_history -> rows in search_queries
  collection     -> the collection_* memory columns
  wishlist       -> the wishlist_* memory columns
  search_history -> the search_* memory columns

Note the underlying collection/wishlist rows themselves are
NOT deleted — those are the user's own catalogue data (what
they own / want), not derived personalization. Consent governs
whether Scentiq *derives from* them, so revoking consent purges
the derivation (the memory paragraph and observations), not the
user's collection.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.user_memory import UserMemory
from app.models.search_query import SearchQuery
from app.schemas.consent import ConsentSettings
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/me/consent", tags=["Consent"])


def _clear_memory_axis(memory: UserMemory, axis: str) -> None:
    """
    Wipe the derived-memory columns for one axis. Called when
    that axis's consent is off. Paragraph, observations,
    timestamp, de-rank counters, and fingerprint all reset,
    so a later regeneration starts clean if consent returns.
    """
    setattr(memory, f"{axis}_paragraph", None)
    setattr(memory, f"{axis}_observations", [])
    setattr(memory, f"{axis}_last_updated", None)
    setattr(memory, f"{axis}_derank_counters", {})
    setattr(memory, f"{axis}_fingerprint", None)


@router.get("", response_model=ConsentSettings)
def get_consent(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's current consent settings."""
    return current_user


@router.put("", response_model=ConsentSettings)
def update_consent(
    payload: ConsentSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the authenticated user's consent settings.

    Expects the full three-boolean state. For every axis whose
    outgoing state is off, both raw inputs and derived memory
    for that axis are purged in this same transaction, so the
    "off means gone" guarantee holds immediately — not only
    after the user next opens their Signature page.
    """
    current_user.consent_collection = payload.consent_collection
    current_user.consent_wishlist = payload.consent_wishlist
    current_user.consent_search_history = payload.consent_search_history

    # Search history: purge the raw logged queries when off.
    if not payload.consent_search_history:
        db.query(SearchQuery).filter(
            SearchQuery.user_id == current_user.id
        ).delete()

    # Derived memory: purge each off-axis's generated paragraph
    # and observations. Only touch the row if one exists — a
    # user who never generated memory has no row to clear.
    memory = db.query(UserMemory).filter(
        UserMemory.user_id == current_user.id
    ).first()
    if memory is not None:
        if not payload.consent_collection:
            _clear_memory_axis(memory, "collection")
        if not payload.consent_wishlist:
            _clear_memory_axis(memory, "wishlist")
        if not payload.consent_search_history:
            _clear_memory_axis(memory, "search")

    db.commit()
    db.refresh(current_user)
    return current_user