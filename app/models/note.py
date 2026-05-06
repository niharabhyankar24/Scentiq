from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class IntensityLevel(enum.Enum):
    """Enum defining how loud a note typically presents."""
    light = "light"
    moderate = "moderate"
    heavy = "heavy"

class PyramidPosition(enum.Enum):
    """Enum defining where a note sits in the scent pyramid."""
    top = "top"
    heart = "heart"
    base = "base"

class NoteSource(enum.Enum):
    """Enum indicating if a note is officially listed or community perceived."""
    official = "official"
    perceived = "perceived"

class Note(Base):
    """Represents an individual scent note with descriptive metadata."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)
    description = Column(String)
    polarizing = Column(Boolean, default=False)
    intensity = Column(Enum(IntensityLevel), nullable=True)

    fragrance_notes = relationship("FragranceNote", back_populates="note")


class FragranceNote(Base):
    """Connector between a fragrance and its notes with position and source."""
    __tablename__ = "fragrance_notes"

    id = Column(Integer, primary_key=True, index=True)
    fragrance_id = Column(Integer, ForeignKey("fragrances.id"), nullable=False)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    pyramid_position = Column(Enum(PyramidPosition), nullable=False)
    source = Column(Enum(NoteSource), nullable=False, default=NoteSource.official)

    fragrance = relationship("Fragrance", back_populates="fragrance_notes")
    note = relationship("Note", back_populates="fragrance_notes")

    __table_args__ = (
        UniqueConstraint("fragrance_id", "note_id", "source", name="unique_fragrance_note_source"),
    )