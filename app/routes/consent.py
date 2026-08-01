"""
Consent routes.

Two endpoints for reading and updating a user's three
consent booleans.

Honesty guarantee enforced here: after any PUT that ends
with consent_search_history == False, every row in
search_queries for that user is deleted in the same
transaction. This is state-based, not transition-based:
if the outgoing state is "off", we guarantee no rows
exist, regardless of how they got there. Off means gone.

Other consent axes (collection, wishlist) do not currently
have derived data to purge — that logic lives in the
memory feature and will be added when memory is built.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.search_query import SearchQuery
from app.schemas.consent import ConsentSettings
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/me/consent", tags=["Consent"])


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

    Expects the full three-boolean state (see schemas/consent.py
    for the reasoning). Whenever the outgoing state has
    search history consent off, all stored search queries
    for this user are deleted in the same transaction. This
    is idempotent: if consent was already off, the delete is
    a no-op against an empty result set.
    """
    current_user.consent_collection = payload.consent_collection
    current_user.consent_wishlist = payload.consent_wishlist
    current_user.consent_search_history = payload.consent_search_history

    if not payload.consent_search_history:
        db.query(SearchQuery).filter(
            SearchQuery.user_id == current_user.id
        ).delete()

    db.commit()
    db.refresh(current_user)
    return current_user