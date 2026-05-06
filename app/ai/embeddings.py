"""
Embedding generation for fragrances.
Converts fragrance data into vector representations
for similarity calculations.
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models.fragrance import Fragrance
from app.models.note import FragranceNote, PyramidPosition
from app.models.note import NoteSource
from app.models.ai_insights import AIInsights

_model = None


def get_model() -> SentenceTransformer:
    """
    Load and return the sentence transformer model.
    Uses singleton pattern — loads once, reuses thereafter.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def build_text_blob(fragrance: Fragrance, db: Session) -> str:
    """
    Build a descriptive text blob for a fragrance.
    Combines official data and AI insights if available.
    """
    parts = []

    parts.append(
        f"{fragrance.brand} {fragrance.name} "
        f"{fragrance.concentration}."
    )

    if fragrance.house_tier:
        parts.append(
            f"{fragrance.house_tier} "
            f"{fragrance.gender_marker} fragrance."
        )

    if fragrance.scent_family:
        parts.append(
            f"Scent family: {fragrance.scent_family.name}."
        )

    def get_notes(position):
        """Fetch official note names for a pyramid position."""
        from app.models.note import Note
        links = db.query(FragranceNote).filter(
            FragranceNote.fragrance_id == fragrance.id,
            FragranceNote.pyramid_position == position,
            FragranceNote.source == NoteSource.official
        ).all()
        note_ids = [link.note_id for link in links]
        if not note_ids:
            return None
        notes = db.query(Note).filter(
            Note.id.in_(note_ids)
        ).all()
        return ", ".join([n.name for n in notes])

    top = get_notes(PyramidPosition.top)
    heart = get_notes(PyramidPosition.heart)
    base = get_notes(PyramidPosition.base)

    if top:
        parts.append(f"Top notes: {top}.")
    if heart:
        parts.append(f"Heart notes: {heart}.")
    if base:
        parts.append(f"Base notes: {base}.")

    insights = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance.id
    ).first()

    if insights and insights.full_insights:
        full = json.loads(insights.full_insights)
        perceived = full.get("perceived_notes", [])
        if perceived:
            perceived_str = ", ".join([
                n["note"] for n in perceived
            ])
            parts.append(
                f"Community perceived notes: {perceived_str}."
            )
        snapshot = full.get("character_snapshot")
        if snapshot:
            parts.append(f"Character: {snapshot}")
        performance = full.get("performance", {})
        if performance:
            parts.append(
                f"Projection: {performance.get('projection')}."
                f" Longevity: {performance.get('longevity')}."
            )

    return " ".join(parts)


def generate_embedding(
    fragrance: Fragrance,
    db: Session
) -> np.ndarray:
    """
    Generate a vector embedding for a fragrance.
    Returns a numpy array of 384 floats.
    """
    model = get_model()
    blob = build_text_blob(fragrance, db)
    embedding = model.encode(blob)
    return embedding


def embedding_to_str(embedding: np.ndarray) -> str:
    """Convert a numpy embedding array to a JSON string."""
    return json.dumps(embedding.tolist())


def str_to_embedding(embedding_str: str) -> np.ndarray:
    """Convert a stored JSON string back to a numpy array."""
    return np.array(json.loads(embedding_str))


def cosine_similarity(
    vec_a: np.ndarray,
    vec_b: np.ndarray
) -> float:
    """
    Calculate cosine similarity between two vectors.
    Returns a float between 0 and 1.
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))