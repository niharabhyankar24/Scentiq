from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.collection import Collection, Wishlist, UserPreferences
from app.models.user import User
from app.schemas.collection import (
    CollectionCreate, CollectionResponse,
    WishlistCreate, WishlistResponse,
    UserPreferencesCreate, UserPreferencesResponse
)
from app.utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/me", tags=["Collection"])


@router.post(
    "/collection",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED
)
def add_to_collection(
    item: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a fragrance to the authenticated user's collection.
    Prevents duplicate entries for the same fragrance.
    """
    existing = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.fragrance_id == item.fragrance_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fragrance already in your collection"
        )
    entry = Collection(
        user_id=current_user.id,
        **item.model_dump()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get(
    "/collection",
    response_model=list[CollectionResponse]
)
def get_collection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return all fragrances in the authenticated user's collection."""
    return db.query(Collection).filter(
        Collection.user_id == current_user.id
    ).all()


@router.delete("/collection/{fragrance_id}")
def remove_from_collection(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a fragrance from the authenticated user's collection
    by fragrance ID.
    """
    entry = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.fragrance_id == fragrance_id
    ).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found in your collection"
        )
    db.delete(entry)
    db.commit()
    return {"message": "Removed from collection"}


@router.post(
    "/wishlist",
    response_model=WishlistResponse,
    status_code=status.HTTP_201_CREATED
)
def add_to_wishlist(
    item: WishlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a fragrance to the authenticated user's wishlist.
    Prevents duplicate wishlist entries.
    """
    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.fragrance_id == item.fragrance_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fragrance already in your wishlist"
        )
    entry = Wishlist(
        user_id=current_user.id,
        **item.model_dump()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get(
    "/wishlist",
    response_model=list[WishlistResponse]
)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return all fragrances in the authenticated user's wishlist."""
    return db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id
    ).all()


@router.post(
    "/preferences",
    response_model=UserPreferencesResponse,
    status_code=status.HTTP_201_CREATED
)
def create_or_update_preferences(
    prefs: UserPreferencesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create or update the authenticated user's taste profile.
    Uses upsert pattern - creates if missing, updates if exists.
    """
    existing = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    if existing:
        for key, value in prefs.model_dump().items():
            setattr(existing, key, value)
        existing.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    entry = UserPreferences(
        user_id=current_user.id,
        **prefs.model_dump()
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get(
    "/preferences",
    response_model=UserPreferencesResponse
)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return the authenticated user's taste profile."""
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.id
    ).first()
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found. Please create them first."
        )
    return prefs

@router.delete("/collection/{fragrance_id}")
def remove_from_collection(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a fragrance from the authenticated user's collection."""
    entry = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.fragrance_id == fragrance_id
    ).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found in your collection"
        )
    db.delete(entry)
    db.commit()
    return {"message": "Removed from collection"}


@router.delete("/wishlist/{fragrance_id}")
def remove_from_wishlist(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a fragrance from the authenticated user's wishlist."""
    entry = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.fragrance_id == fragrance_id
    ).first()
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found in your wishlist"
        )
    db.delete(entry)
    db.commit()
    return {"message": "Removed from wishlist"}