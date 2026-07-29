"""
Consent routes.

Two endpoints for reading and updating a user's three
consent booleans.

Honesty guarantee enforced here: if a PUT is turning
consent_search_history from True to False, every row in
search_queries for that user is deleted in the same
transaction. Withdrawal means the data is gone.

Other consent axes (collection, wishlist) do not currently
have derived data to purge on revoke — that logic lives in
the memory feature and will be added when memory is built.
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
    for the reasoning). If search history consent is being
    revoked in this update, all stored search queries for
    this user are deleted in the same transaction.
    """
    revoking_search_history = (
        current_user.consent_search_history
        and not payload.consent_search_history
    )

    current_user.consent_collection = payload.consent_collection
    current_user.consent_wishlist = payload.consent_wishlist
    current_user.consent_search_history = payload.consent_search_history

    if revoking_search_history:
        db.query(SearchQuery).filter(
            SearchQuery.user_id == current_user.id
        ).delete()

    db.commit()
    db.refresh(current_user)
    return current_user