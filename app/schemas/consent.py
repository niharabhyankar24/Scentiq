"""
Consent schemas.

Shape validation for the GET and PUT endpoints on
/api/me/consent. Three booleans, one per axis.

Request and response use the same shape: a full snapshot
of all three axes. PUT expects all three fields — the
client sends the desired full state, not a partial diff.
Simpler contract, avoids ambiguity about "field not sent
means keep existing" vs "set to false."
"""

from pydantic import BaseModel, ConfigDict


class ConsentSettings(BaseModel):
    """The three consent booleans. Used for both request and response."""

    consent_collection: bool
    consent_wishlist: bool
    consent_search_history: bool

    model_config = ConfigDict(from_attributes=True)