"""
SearchQuery model.

One row per search event, written ONLY when the user is
authenticated AND has consent_search_history set to true.
Anonymous searches and searches by non-consenting users
are never logged.

When a user revokes search consent, every row for that
user is deleted in the same transaction as the consent
flip. Withdrawal means the data is gone, not retained.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    query = Column(String, nullable=False)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    user = relationship("User", back_populates="search_queries")