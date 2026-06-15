from pydantic import BaseModel, model_validator
from typing import Optional
from typing import Annotated
from pydantic.functional_validators import BeforeValidator
from typing import Literal, Optional

def empty_to_none(v):
    if v == 0 or v == "":
        return None
    return v

NullableInt = Annotated[Optional[int], BeforeValidator(empty_to_none)]

class ScentFamilyCreate(BaseModel):
    """Represents a top-level scent category like Oud or Fresh."""
    name: str
    description: Optional[str] = None
    typical_occasions: Optional[str] = None

class ScentFamilyResponse(BaseModel):
    """Represents a top-level scent category like Oud or Fresh."""
    id: int
    name: str
    description: Optional[str] = None
    typical_occasions: Optional[str] = None

    class Config:
        from_attributes = True

class FragranceCreate(BaseModel):
    """Represents a single perfume entry in the master catalogue."""
    brand: str
    name: str
    concentration: Optional[str] = None
    release_year: Optional[int] = None
    gender_marker: Optional[str] = None
    house_tier: Optional[str] = None
    official_description: Optional[str] = None
    image_url: Optional[str] = None
    scent_family_id: NullableInt = None
    secondary_scent_family_id: NullableInt = None
    parent_fragrance_id: NullableInt = None
    refresh_interval_days: Optional[int] = 90

class FragranceResponse(BaseModel):
    """Represents a single perfume entry in the master catalogue."""
    id: int
    brand: str
    name: str
    concentration: Optional[str] = None
    release_year: Optional[int] = None
    gender_marker: Optional[str] = None
    house_tier: Optional[str] = None
    official_description: Optional[str] = None
    image_url: Optional[str] = None
    scent_family_id: Optional[int] = None

    class Config:
        from_attributes = True

class AdminNoteAssignment(BaseModel):
    """
    Request body for assigning a note to a fragrance.

    Exactly one of note_id or note_name must be provided.
    Fields prefixed with note_ (other than note_id) apply
    only when creating a new note inline via note_name.
    """
    pyramid_position: str  # "top" | "heart" | "base"
    note_id: Optional[int] = None

    # Fields for creating a new note inline.
    note_name: Optional[str] = None
    note_category: Optional[str] = None
    note_description: Optional[str] = None
    note_polarizing: Optional[bool] = False
    note_intensity: Optional[Literal["light", "moderate", "heavy"]] = None

    @model_validator(mode="after")
    def require_id_or_name(self):
        if not self.note_id and not self.note_name:
            raise ValueError("Provide either note_id or note_name")
        if self.note_id and self.note_name:
            raise ValueError("Provide note_id or note_name, not both")
        if self.note_name and not self.note_category:
            raise ValueError(
                "note_category required when creating a new note"
            )
        return self
    
class AdminNoteUpdate(BaseModel):
    """
    Partial update to a Note. All fields optional;
    only provided fields are applied.
    """
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    polarizing: Optional[bool] = None
    intensity: Optional[Literal["light", "moderate", "heavy"]] = None