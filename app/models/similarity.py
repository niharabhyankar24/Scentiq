"""
SQLAlchemy model for storing pairwise similarity scores
between fragrances.
"""

from sqlalchemy import (
    Column, Integer, Float, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class SimilarityScore(Base):
    """
    Stores pre-calculated similarity between two fragrances.
    Only pairs above minimum threshold are stored.
    Partitioned by scent family for efficient querying.
    """

    __tablename__ = "similarity_scores"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_a_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False
    )
    fragrance_b_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False
    )
    similarity_score = Column(Float, nullable=False)
    scent_family_id = Column(
        Integer,
        ForeignKey("scent_families.id"),
        nullable=True
    )
    last_calculated = Column(
        DateTime,
        default=datetime.utcnow
    )

    fragrance_a = relationship(
        "Fragrance",
        foreign_keys=[fragrance_a_id]
    )
    fragrance_b = relationship(
        "Fragrance",
        foreign_keys=[fragrance_b_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "fragrance_a_id",
            "fragrance_b_id",
            name="unique_fragrance_pair"
        ),
    )