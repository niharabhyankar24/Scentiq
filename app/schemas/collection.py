from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.collection import BottleStatus, WishlistPriority


class CollectionCreate(BaseModel):
    """Schema for adding a fragrance to a user's collection."""

    fragrance_id: int
    bottle_status: Optional[BottleStatus] = BottleStatus.full
    snapshot_summary: Optional[str] = Field(
        None, max_length=200
    )
    personal_rating: Optional[int] = Field(
        None, ge=1, le=10
    )
    personal_notes: Optional[str] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[datetime] = None


class CollectionResponse(BaseModel):
    """Schema for returning a collection entry to the client."""

    id: int
    user_id: int
    fragrance_id: int
    date_added: datetime
    bottle_status: Optional[BottleStatus]
    snapshot_summary: Optional[str]
    personal_rating: Optional[int]
    personal_notes: Optional[str]
    purchase_price: Optional[float]

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True


class WishlistCreate(BaseModel):
    """Schema for adding a fragrance to a user's wishlist."""

    fragrance_id: int
    priority: Optional[WishlistPriority] = WishlistPriority.medium
    notes: Optional[str] = None
    budget_ceiling: Optional[float] = None


class WishlistResponse(BaseModel):
    """Schema for returning a wishlist entry to the client."""

    id: int
    user_id: int
    fragrance_id: int
    date_added: datetime
    priority: Optional[WishlistPriority]
    notes: Optional[str]
    budget_ceiling: Optional[float]

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True


class UserPreferencesCreate(BaseModel):
    """Schema for creating or updating a user's taste profile."""

    favourite_notes: Optional[str] = None
    disliked_notes: Optional[str] = None
    preferred_families: Optional[str] = None
    preferred_occasions: Optional[str] = None
    preferred_seasons: Optional[str] = None
    projection_preference: Optional[str] = None
    budget_range: Optional[str] = None


class UserPreferencesResponse(BaseModel):
    """Schema for returning a user's taste profile."""

    id: int
    user_id: int
    favourite_notes: Optional[str]
    disliked_notes: Optional[str]
    preferred_families: Optional[str]
    preferred_occasions: Optional[str]
    preferred_seasons: Optional[str]
    projection_preference: Optional[str]
    budget_range: Optional[str]
    last_updated: datetime

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True