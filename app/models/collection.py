from sqlalchemy import (
    Column, Integer, String, Float,
    ForeignKey, DateTime, CheckConstraint, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class BottleStatus(enum.Enum):
    """Enum representing how full a bottle is."""

    full = "full"
    mostly_full = "mostly_full"
    half = "half"
    low = "low"
    empty = "empty"


class WishlistPriority(enum.Enum):
    """Enum representing how urgently a user wants a fragrance."""

    high = "high"
    medium = "medium"
    low = "low"


class Collection(Base):
    """
    Represents a fragrance the user owns.
    Links a user to a fragrance with personal metadata.
    """

    __tablename__ = "collection"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    fragrance_id = Column(
        Integer, ForeignKey("fragrances.id"), nullable=False
    )
    date_added = Column(DateTime, default=datetime.utcnow)
    bottle_status = Column(
        Enum(BottleStatus), default=BottleStatus.full
    )
    snapshot_summary = Column(String(200), nullable=True)
    personal_rating = Column(Integer, nullable=True)
    personal_notes = Column(String, nullable=True)
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="collection")
    fragrance = relationship(
        "Fragrance", back_populates="collection"
    )

    __table_args__ = (
        CheckConstraint(
            "personal_rating >= 1 AND personal_rating <= 10",
            name="valid_personal_rating"
        ),
    )


class Wishlist(Base):
    """
    Represents a fragrance the user wants to buy.
    Links a user to a fragrance with intent metadata.
    """

    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    fragrance_id = Column(
        Integer, ForeignKey("fragrances.id"), nullable=False
    )
    date_added = Column(DateTime, default=datetime.utcnow)
    priority = Column(
        Enum(WishlistPriority), default=WishlistPriority.medium
    )
    notes = Column(String, nullable=True)
    budget_ceiling = Column(Float, nullable=True)

    user = relationship("User", back_populates="wishlist")
    fragrance = relationship(
        "Fragrance", back_populates="wishlist"
    )


class UserPreferences(Base):
    """
    Stores a user's taste profile.
    One row per user. Drives recommendations in v2.
    """

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )
    favourite_notes = Column(String, nullable=True)
    disliked_notes = Column(String, nullable=True)
    preferred_families = Column(String, nullable=True)
    preferred_occasions = Column(String, nullable=True)
    preferred_seasons = Column(String, nullable=True)
    projection_preference = Column(String, nullable=True)
    budget_range = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User", back_populates="preferences"
    )