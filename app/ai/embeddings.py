"""
Embedding generation for fragrances.
Converts fragrance data into vector representations
for similarity calculations.
"""

import json
from typing import Optional
import numpy as np
from sqlalchemy.orm import Session
from app.models.fragrance import Fragrance
from app.models.note import (
    FragranceNote, PyramidPosition, NoteSource
)
from app.models.note import NoteSource
from app.models.ai_insights import AIInsights
from app.models.pricing import PriceListing

_model = None


def get_model():
    """
    Load and return the sentence transformer model.
    Uses singleton pattern — loads once, reuses thereafter.
    """
    global _model
    if _model is None:
        # Lazy import: only triggers when a similarity
        # endpoint is actually called. Keeps idle memory low.
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2")
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

def _get_notes_by_position(
    db: Session,
    fragrance_id: int,
    position: PyramidPosition
) -> str:
    """Return comma-separated official note names for a position."""
    links = db.query(FragranceNote).filter(
        FragranceNote.fragrance_id == fragrance_id,
        FragranceNote.pyramid_position == position,
        FragranceNote.source == NoteSource.official
    ).all()
    if not links:
        return ""
    return ", ".join(link.note.name for link in links)


def _get_cheapest_price_per_ml(
    db: Session,
    fragrance_id: int
) -> Optional[float]:
    """
    Return the lowest stored price_per_ml across all
    price listings for this fragrance, or None if no
    pricing data exists.
    """
    listings = db.query(PriceListing).filter(
        PriceListing.fragrance_id == fragrance_id,
        PriceListing.price_per_ml.isnot(None)
    ).all()
    if not listings:
        return None
    return round(
        min(listing.price_per_ml for listing in listings),
        2
    )   

def _price_tier(price_per_ml: Optional[float]) -> str:
    """Categorize price into a human-readable tier."""
    if price_per_ml is None:
        return "unknown"
    if price_per_ml < 1:
        return "budget"
    if price_per_ml < 3:
        return "mid-range"
    if price_per_ml < 8:
        return "premium"
    return "luxury"


def build_fragrance_text(
    db: Session,
    fragrance: Fragrance,
    insights: Optional[AIInsights]
) -> str:
    """
    Build the structured text representation of a fragrance
    that will be fed into the embedding model.

    Order matters: identity, scent family, character (most
    semantically dense), notes, performance, sentiment,
    occasions, price. Missing fields are gracefully omitted
    so partial data still produces useful embeddings.
    """
    parts = []

    # 1. Identity.
    identity = f"{fragrance.brand} {fragrance.name}"
    if fragrance.concentration:
        identity += f". {fragrance.concentration}"
    parts.append(identity + ".")

    # 2. Scent family.
    if fragrance.scent_family:
        parts.append(
            f"Scent family: {fragrance.scent_family.name}."
        )

    # 3. Character (most dense — front-loaded).
    # Prefer the richer character_full when available.
    if insights:
        character = insights.character_full or insights.snapshot_draft
        if character:
            parts.append(f"Character: {character}")
            
    # 4. Notes pyramid.
    top = _get_notes_by_position(
        db, fragrance.id, PyramidPosition.top
    )
    heart = _get_notes_by_position(
        db, fragrance.id, PyramidPosition.heart
    )
    base = _get_notes_by_position(
        db, fragrance.id, PyramidPosition.base
    )
    if top:
        parts.append(f"Top notes: {top}.")
    if heart:
        parts.append(f"Heart notes: {heart}.")
    if base:
        parts.append(f"Base notes: {base}.")

    # 5-7. Insights-derived content (performance, sentiment,
    # occasions).
    if insights and insights.full_insights:
        try:
            full = json.loads(insights.full_insights)
        except (json.JSONDecodeError, TypeError):
            full = {}

        # Performance.
        perf = full.get("performance") or {}
        perf_parts = []
        if perf.get("projection"):
            perf_parts.append(f"{perf['projection']} projection")
        if perf.get("sillage"):
            perf_parts.append(f"{perf['sillage']} sillage")
        if perf.get("longevity"):
            perf_parts.append(f"{perf['longevity']} longevity")
        if perf_parts:
            parts.append(f"Performance: {', '.join(perf_parts)}.")

        # Sentiment.
        if insights.sentiment:
            parts.append(f"Sentiment: {insights.sentiment}.")

        # Occasions.
        occasions = full.get("occasions")
        if occasions and isinstance(occasions, list):
            parts.append(
                f"Best for: {', '.join(occasions)}."
            )

    # 8. Pricing.
    price_per_ml = _get_cheapest_price_per_ml(db, fragrance.id)
    if price_per_ml is not None:
        tier = _price_tier(price_per_ml)
        parts.append(
            f"Price: {tier} (approx ${price_per_ml} per ml)."
        )

    return " ".join(parts)


def generate_embedding(
    db: Session,
    fragrance_id: int
) -> Optional[list[float]]:
    """
    Generate an embedding vector for a fragrance.

    Loads the fragrance and its AIInsights, builds a
    structured text representation via build_fragrance_text,
    and encodes it via the sentence transformer model.

    Returns a 384-dimensional list of floats, or None
    if the fragrance is not found.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        return None

    insights = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance_id
    ).first()

    text = build_fragrance_text(db, fragrance, insights)
    model = get_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()