from pydantic import BaseModel
from typing import Optional
from app.models.note import IntensityLevel, PyramidPosition, NoteSource


class NoteCreate(BaseModel):
    """Schema for creating a new scent note."""

    name: str
    category: str
    description: Optional[str] = None
    polarizing: Optional[bool] = False
    intensity: Optional[IntensityLevel] = None


class NoteResponse(BaseModel):
    """Schema for returning a scent note to the client."""

    id: int
    name: str
    category: str
    description: Optional[str]
    polarizing: bool
    intensity: Optional[IntensityLevel]

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True


class FragranceNoteCreate(BaseModel):
    """Schema for linking a note to a fragrance."""

    note_id: int
    pyramid_position: PyramidPosition
    source: Optional[NoteSource] = NoteSource.official


class FragranceNoteResponse(BaseModel):
    """Schema for returning a fragrance-note link to the client."""

    id: int
    fragrance_id: int
    note_id: int
    pyramid_position: PyramidPosition
    source: NoteSource

    class Config:
        """Pydantic config to support SQLAlchemy model reading."""

        from_attributes = True