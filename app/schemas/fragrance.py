from pydantic import BaseModel
from typing import Optional
from typing import Annotated
from pydantic.functional_validators import BeforeValidator

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