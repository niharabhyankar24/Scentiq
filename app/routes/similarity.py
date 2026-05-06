"""
API routes for embedding generation, similarity calculation,
and redundancy detection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.dependencies import get_current_user
from app.ai.similarity import (
    embed_fragrance,
    calculate_similarity_for_fragrance,
    get_similar_fragrances,
    check_collection_redundancy
)

router = APIRouter(tags=["Similarity"])


@router.post("/fragrances/{fragrance_id}/embed")
def generate_fragrance_embedding(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate and store embedding for a fragrance.
    Must be run before similarity calculation.
    """
    try:
        embed_fragrance(fragrance_id, db)
        return {
            "message": (
                f"Embedding generated for "
                f"fragrance {fragrance_id}."
            )
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/fragrances/{fragrance_id}/calculate-similarity"
)
def calculate_similarity(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate and store similarity scores between this
    fragrance and others in the same scent family.
    """
    try:
        results = calculate_similarity_for_fragrance(
            fragrance_id, db
        )
        return {
            "fragrance_id": fragrance_id,
            "comparisons_stored": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/fragrances/{fragrance_id}/similar")
def get_similar(
    fragrance_id: int,
    min_score: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    Return pre-calculated similar fragrances sorted
    by similarity score. Use min_score to filter results.
    """
    results = get_similar_fragrances(
        fragrance_id, db, min_score=min_score
    )
    if not results:
        return {
            "fragrance_id": fragrance_id,
            "message": (
                "No similar fragrances found above threshold. "
                "Run calculate-similarity first."
            ),
            "similar": []
        }
    return {
        "fragrance_id": fragrance_id,
        "similar": results
    }


@router.get(
    "/fragrances/{fragrance_id}/redundancy-check"
)
def redundancy_check(
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a fragrance overlaps significantly with
    anything in the authenticated user's collection.
    """
    result = check_collection_redundancy(
        fragrance_id, current_user.id, db
    )
    return result