"""
SQLAlchemy model for storing AI generated fragrance insights.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Date
)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

from pgvector.sqlalchemy import Vector

class AIInsights(Base):
    """
    Stores AI generated analysis for a fragrance.
    Updated independently from core fragrance data.
    """

    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_id = Column(
        Integer,
        ForeignKey("fragrances.id"),
        nullable=False,
        unique=True
    )
    perceived_summary = Column(String, nullable=True)
    snapshot_draft = Column(String(200), nullable=True)
    sentiment = Column(String, nullable=True)
    confidence_score = Column(Float, default=0.0)
    full_insights = Column(Text, nullable=True)
    sources_used = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    character_full = Column(Text, nullable=True)
    
    fragrance = relationship("Fragrance", back_populates="insights")
    analysis_refresh_due = Column(Date, nullable=True)
    embedding = Column(Vector(384), nullable=True)
    