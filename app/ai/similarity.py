"""
Similarity calculation and redundancy detection engine.
Calculates, stores, and queries fragrance similarity scores.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.fragrance import Fragrance
from app.models.similarity import SimilarityScore
from app.ai.embeddings import (
    generate_embedding,
    embedding_to_str,
    str_to_embedding,
    cosine_similarity
)
from datetime import datetime

MINIMUM_THRESHOLD = 0.5
REDUNDANCY_THRESHOLD = 0.60


def embed_fragrance(
    fragrance_id: int,
    db: Session
) -> str:
    """
    Generate and store embedding for a fragrance.
    Returns the stored JSON string.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise ValueError(
            f"Fragrance {fragrance_id} not found."
        )
    embedding = generate_embedding(fragrance, db)
    fragrance.embedding = embedding_to_str(embedding)
    db.commit()
    return fragrance.embedding


def calculate_similarity_for_fragrance(
    fragrance_id: int,
    db: Session
) -> list[dict]:
    """
    Calculate similarity between a fragrance and all others
    in the same scent family. Stores results above threshold.
    Returns list of similarity results.
    """
    target = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not target or not target.embedding:
        raise ValueError(
            f"Fragrance {fragrance_id} not found "
            f"or has no embedding. Run embed first."
        )

    target_vec = str_to_embedding(target.embedding)

    candidates = db.query(Fragrance).filter(
        Fragrance.id != fragrance_id,
        Fragrance.scent_family_id == target.scent_family_id,
        Fragrance.embedding != None
    ).all()

    results = []
    for candidate in candidates:
        candidate_vec = str_to_embedding(candidate.embedding)
        score = cosine_similarity(target_vec, candidate_vec)

        if score < MINIMUM_THRESHOLD:
            continue

        frag_a_id = min(fragrance_id, candidate.id)
        frag_b_id = max(fragrance_id, candidate.id)

        existing = db.query(SimilarityScore).filter(
            SimilarityScore.fragrance_a_id == frag_a_id,
            SimilarityScore.fragrance_b_id == frag_b_id
        ).first()

        if existing:
            existing.similarity_score = score
            existing.last_calculated = datetime.utcnow()
        else:
            record = SimilarityScore(
                fragrance_a_id=frag_a_id,
                fragrance_b_id=frag_b_id,
                similarity_score=score,
                scent_family_id=target.scent_family_id
            )
            db.add(record)

        results.append({
            "fragrance_id": candidate.id,
            "brand": candidate.brand,
            "name": candidate.name,
            "concentration": candidate.concentration,
            "similarity_score": round(score, 4)
        })

    db.commit()
    results.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )
    return results


def get_similar_fragrances(
    fragrance_id: int,
    db: Session,
    min_score: float = MINIMUM_THRESHOLD,
    limit: int = 10
) -> list[dict]:
    """
    Return pre-calculated similar fragrances sorted
    by similarity score descending.
    """
    records = db.query(SimilarityScore).filter(
        or_(
            SimilarityScore.fragrance_a_id == fragrance_id,
            SimilarityScore.fragrance_b_id == fragrance_id
        ),
        SimilarityScore.similarity_score >= min_score
    ).order_by(
        SimilarityScore.similarity_score.desc()
    ).limit(limit).all()

    results = []
    for record in records:
        other_id = (
            record.fragrance_b_id
            if record.fragrance_a_id == fragrance_id
            else record.fragrance_a_id
        )
        other = db.query(Fragrance).filter(
            Fragrance.id == other_id
        ).first()
        if other:
            results.append({
                "fragrance_id": other.id,
                "brand": other.brand,
                "name": other.name,
                "concentration": other.concentration,
                "similarity_score": record.similarity_score
            })
    return results


def check_collection_redundancy(
    fragrance_id: int,
    user_id: int,
    db: Session
) -> dict:
    """
    Check if a fragrance is redundant with anything in
    the user's collection. Returns warning if score
    exceeds redundancy threshold.
    """
    from app.models.collection import Collection

    collection_items = db.query(Collection).filter(
        Collection.user_id == user_id
    ).all()

    if not collection_items:
        return {
            "redundant": False,
            "message": "Collection is empty.",
            "matches": []
        }

    collection_ids = [
        item.fragrance_id for item in collection_items
    ]

    target = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not target or not target.embedding:
        return {
            "redundant": False,
            "message": "Fragrance has no embedding yet.",
            "matches": []
        }

    target_vec = str_to_embedding(target.embedding)
    matches = []

    for coll_id in collection_ids:
        if coll_id == fragrance_id:
            continue
        owned = db.query(Fragrance).filter(
            Fragrance.id == coll_id
        ).first()
        if not owned or not owned.embedding:
            continue
        owned_vec = str_to_embedding(owned.embedding)
        score = cosine_similarity(target_vec, owned_vec)
        if score >= REDUNDANCY_THRESHOLD:
            matches.append({
                "fragrance_id": owned.id,
                "brand": owned.brand,
                "name": owned.name,
                "concentration": owned.concentration,
                "similarity_score": round(score, 4)
            })

    matches.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    if matches:
        return {
            "redundant": True,
            "message": (
                f"This fragrance is very similar to "
                f"{len(matches)} item(s) in your collection."
            ),
            "matches": matches
        }
    return {
        "redundant": False,
        "message": "No significant overlap with your collection.",
        "matches": []
    }