from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class User(Base):
    """Represents a registered user account."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False, nullable=False)

    # --- v2 consent axes ---
    consent_collection = Column(Boolean, default=False, nullable=False)
    consent_wishlist = Column(Boolean, default=False, nullable=False)
    consent_search_history = Column(Boolean, default=False, nullable=False)

    # --- Existing relationships ---
    collection = relationship(
        "Collection",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    wishlist = relationship(
        "Wishlist",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # --- v2 relationships ---
    memory = relationship(
        "UserMemory",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    search_queries = relationship(
        "SearchQuery",
        back_populates="user",
        cascade="all, delete-orphan"
    )