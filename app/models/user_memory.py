"""
UserMemory model.

One row per user. Holds everything the AI has derived
about that user, split into three axes:

  - collection: derived from owned fragrances and ratings
  - wishlist:   derived from wanted fragrances and priorities
  - search:     derived from search history

Each axis stores four things:
  1. paragraph        — prose summary shown to the user
  2. observations     — pruneable structured bullets
  3. last_updated     — when this section was regenerated
  4. derank_counters  — how many times each tag has been
                        deleted from this axis (for the
                        de-rank threshold of 2)

The row is created lazily on the user's first opt-in.
When a user opts OUT of an axis, that axis's four fields
are cleared but the row itself stays (the other axes may
still be in use).
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # --- Collection axis ---
    collection_paragraph = Column(Text, nullable=True)
    collection_observations = Column(
        JSONB, nullable=False, default=list
    )
    collection_last_updated = Column(DateTime, nullable=True)
    collection_derank_counters = Column(
        JSONB, nullable=False, default=dict
    )

    # --- Wishlist axis ---
    wishlist_paragraph = Column(Text, nullable=True)
    wishlist_observations = Column(
        JSONB, nullable=False, default=list
    )
    wishlist_last_updated = Column(DateTime, nullable=True)
    wishlist_derank_counters = Column(
        JSONB, nullable=False, default=dict
    )

    # --- Search axis ---
    search_paragraph = Column(Text, nullable=True)
    search_observations = Column(
        JSONB, nullable=False, default=list
    )
    search_last_updated = Column(DateTime, nullable=True)
    search_derank_counters = Column(
        JSONB, nullable=False, default=dict
    )

    user = relationship("User", back_populates="memory")