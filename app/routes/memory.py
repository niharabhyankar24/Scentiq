"""
Memory routes.

Two endpoints powering the memory feature:

  GET  /api/me/memory
       Regenerates any stale axes (lazy) and returns the
       current memory shape. Skips axes the user hasn't
       consented to. Handles rate limiting, Claude failure,
       and fingerprint-based skipping internally.

  DELETE /api/me/memory/observations/{axis}/{observation_id}
       Removes one observation from an axis paragraph and
       increments its tag's delete counter for that axis.
       When the counter reaches DERANK_THRESHOLD, that tag
       is effectively de-ranked: future regenerations avoid
       it, and if it slips through it's filtered out.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.models.user import User
from app.models.user_memory import UserMemory
from app.schemas.memory import MemoryResponse
from app.utils.dependencies import get_current_user
from app.ai.memory_generator import regenerate_memory


router = APIRouter(prefix="/me/memory", tags=["Memory"])


# --- GET /api/me/memory -----------------------------------
# Lazy regeneration. The generator itself decides which
# axes need Claude calls (by fingerprint) and which don't.
# We just call it and return the shape.

@router.get("", response_model=MemoryResponse)
def get_memory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the user's memory across all opted-in axes.

    Regenerates any stale axes in the background of this
    request (lazy). If nothing is stale, no Claude calls
    happen and this returns cached content in a few ms.
    """
    return regenerate_memory(current_user, db)


# --- DELETE observation -----------------------------------
# The URL takes both axis and observation_id because ids
# are UUIDs assigned per regeneration — global uniqueness
# is not guaranteed across axes. Passing axis explicitly
# keeps the lookup unambiguous.

_VALID_AXES = {"collection", "wishlist", "search"}


@router.delete(
    "/observations/{axis}/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_observation(
    axis: str,
    observation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete one observation from the given axis. Increments
    the derank counter for that observation's tag. Returns
    204 No Content on success.

    Errors:
      400 — invalid axis name.
      403 — user has not consented to this axis (so it
            shouldn't have observations to delete).
      404 — no memory row, or no matching observation id.
    """
    if axis not in _VALID_AXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid axis: {axis}",
        )

    # Consent gate. If the user opted out of this axis,
    # there is nothing legitimate to delete. This also
    # defends against a stale frontend still showing
    # observations from a since-revoked axis.
    consent_flag = getattr(current_user, f"consent_{axis}"
                          if axis != "search"
                          else "consent_search_history")
    if not consent_flag:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Consent for {axis} is off.",
        )

    memory_row = db.query(UserMemory).filter(
        UserMemory.user_id == current_user.id
    ).first()
    if not memory_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No memory yet — try opening the memory page first.",
        )

    # --- Locate the observation ---
    observations = getattr(
        memory_row, f"{axis}_observations", []
    ) or []
    target = None
    remaining = []
    for obs in observations:
        if obs.get("id") == observation_id:
            target = obs
        else:
            remaining.append(obs)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation {observation_id} not found in {axis}.",
        )

    # --- Bump the derank counter for this tag ---
    counters = dict(
        getattr(memory_row, f"{axis}_derank_counters", {}) or {}
    )
    tag = (target.get("tag") or "").strip()
    if tag:
        counters[tag] = counters.get(tag, 0) + 1

    # --- Persist the changes ---
    # JSONB columns need flag_modified when we replace them
    # with a new object; SQLAlchemy otherwise misses the
    # mutation and skips the UPDATE.
    setattr(memory_row, f"{axis}_observations", remaining)
    setattr(memory_row, f"{axis}_derank_counters", counters)
    flag_modified(memory_row, f"{axis}_observations")
    flag_modified(memory_row, f"{axis}_derank_counters")

    # Clear this axis's fingerprint so the next memory read
    # regenerates the paragraph instead of serving the cached
    # one. Without this, the fingerprint still matches the
    # source data, regeneration is skipped, and the paragraph
    # keeps describing the observation the user just deleted.
    # (Note: the *theme* only disappears once its tag crosses
    # the de-rank threshold of 2 — a single deletion refreshes
    # the paragraph but may still touch the theme, by design.)
    setattr(memory_row, f"{axis}_fingerprint", None)

    db.commit()

    # 204 means "success, no body" — that's the standard
    # response for a successful DELETE that has nothing
    # meaningful to return.
    return None