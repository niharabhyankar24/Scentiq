"""
Memory schemas.

Shapes for the memory endpoints. Structure:

  MemoryResponse
    ├── collection: AxisMemory | None
    ├── wishlist:   AxisMemory | None
    └── search:     AxisMemory | None

  AxisMemory
    ├── paragraph:     str (the prose summary)
    ├── observations:  list[Observation]
    └── last_updated:  datetime

  Observation
    ├── id:   int (unique within its axis paragraph)
    ├── text: str (what the user reads)
    └── tag:  str (used for de-rank counters)

Each axis is Optional at the top level because a user may
have opted into only one or two axes. Nothing is returned
for axes the user hasn't consented to.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --- Observation ------------------------------------------
# The smallest unit of memory. The user sees `text`, deletion
# targets `id`, and the de-rank counter is keyed on `tag`.
class Observation(BaseModel):
    id: str
    text: str
    tag: str

    model_config = ConfigDict(from_attributes=True)


# --- Per-axis memory --------------------------------------
# One instance per opted-in axis. Bundles the prose paragraph
# and its list of individually-deletable observations.
class AxisMemory(BaseModel):
    paragraph: str
    observations: list[Observation]
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Full memory response ---------------------------------
# The top-level shape returned by GET /api/me/memory.
# Each axis field is None when the user hasn't opted in,
# so the frontend can render only the sections that exist.
class MemoryResponse(BaseModel):
    collection: Optional[AxisMemory] = None
    wishlist: Optional[AxisMemory] = None
    search: Optional[AxisMemory] = None

    model_config = ConfigDict(from_attributes=True)