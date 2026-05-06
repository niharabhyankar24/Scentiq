"""
Stage 1 exploration script for embeddings and similarity.
Run with: python explore_embeddings.py
Shows every intermediate output so you can understand
what the embedding pipeline actually produces.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import app.models.collection
import app.models.user
import app.models.note
import app.models.ai_insights
import app.models.pricing

import numpy as np
import json
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal
from app.models.fragrance import Fragrance
from app.models.note import FragranceNote, PyramidPosition, NoteSource
from app.models.ai_insights import AIInsights


def build_text_blob(fragrance, db) -> str:
    """
    Build a descriptive text blob for a fragrance.
    This is what gets converted into an embedding vector.
    Shows every component being assembled.
    """
    parts = []

    # Basic identity
    parts.append(
        f"{fragrance.brand} {fragrance.name} "
        f"{fragrance.concentration}."
    )

    # House tier and gender
    if fragrance.house_tier:
        parts.append(
            f"{fragrance.house_tier} {fragrance.gender_marker} "
            f"fragrance."
        )

    # Scent family
    if fragrance.scent_family:
        parts.append(
            f"Scent family: {fragrance.scent_family.name}."
        )

    # Official notes by pyramid position
    def get_notes(position):
        """Fetch note names for a pyramid position."""
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

    # AI perceived character if available
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
                f"Projection: {performance.get('projection')}. "
                f"Longevity: {performance.get('longevity')}."
            )

    return " ".join(parts)


def cosine_similarity(vec_a, vec_b) -> float:
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


def main():
    """
    Run the full exploration pipeline with visible outputs
    at every stage.
    """
    db = SessionLocal()

    try:
        # ----------------------------------------
        # STAGE 1 — Load the model
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 1 — Loading sentence transformer model")
        print("="*50)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded successfully.")
        print(f"Embedding dimensions: "
              f"{model.get_sentence_embedding_dimension()}")

        # ----------------------------------------
        # STAGE 2 — Pick two fragrances to compare
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 2 — Loading fragrances from database")
        print("="*50)

        fragrances = db.query(Fragrance).limit(4).all()
        if len(fragrances) < 2:
            print("Need at least 2 fragrances. Run seed.py first.")
            return

        for f in fragrances:
            print(f"  ID {f.id}: {f.brand} {f.name} "
                  f"{f.concentration}")

        # ----------------------------------------
        # STAGE 3 — Build text blobs
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 3 — Building text blobs")
        print("="*50)

        blobs = []
        for f in fragrances:
            blob = build_text_blob(f, db)
            blobs.append(blob)
            print(f"\n{f.brand} {f.name} {f.concentration}:")
            print(f"  {blob}")

        # ----------------------------------------
        # STAGE 4 — Generate embeddings
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 4 — Generating embeddings")
        print("="*50)

        embeddings = model.encode(blobs)
        print(f"Generated {len(embeddings)} embeddings.")
        print(f"Each embedding shape: {embeddings[0].shape}")
        print(f"\nFirst 10 numbers of first embedding:")
        print(f"  {embeddings[0][:10].tolist()}")
        print(f"\nMin value: {embeddings[0].min():.4f}")
        print(f"Max value: {embeddings[0].max():.4f}")
        print(f"Mean value: {embeddings[0].mean():.4f}")

        # ----------------------------------------
        # STAGE 5 — Calculate pairwise similarities
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 5 — Calculating pairwise cosine similarities")
        print("="*50)

        print("\nSimilarity matrix:")
        print(f"{'':30}", end="")
        for f in fragrances:
            label = f"{f.name[:12]:>14}"
            print(label, end="")
        print()

        for i, f_a in enumerate(fragrances):
            label = f"{f_a.brand} {f_a.name}"[:30]
            print(f"{label:30}", end="")
            for j, f_b in enumerate(fragrances):
                score = cosine_similarity(
                    embeddings[i], embeddings[j]
                )
                print(f"{score:>14.3f}", end="")
            print()

        # ----------------------------------------
        # STAGE 6 — Find most similar pairs
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 6 — Most similar pairs above threshold 0.5")
        print("="*50)

        pairs = []
        for i in range(len(fragrances)):
            for j in range(i + 1, len(fragrances)):
                score = cosine_similarity(
                    embeddings[i], embeddings[j]
                )
                pairs.append((
                    fragrances[i], fragrances[j], score
                ))

        pairs.sort(key=lambda x: x[2], reverse=True)

        found = False
        for f_a, f_b, score in pairs:
            if score >= 0.5:
                found = True
                print(
                    f"\n{f_a.brand} {f_a.name} "
                    f"<-> {f_b.brand} {f_b.name}"
                )
                print(f"  Similarity score: {score:.4f}")
                if score >= 0.75:
                    print(f"  ⚠ REDUNDANCY WARNING — "
                          f"very similar, may overlap in collection")
                elif score >= 0.6:
                    print(f"  Similar territory — "
                          f"worth knowing about")
                else:
                    print(f"  Loosely related")

        if not found:
            print("No pairs above 0.5 threshold.")
            print("All pairs:")
            for f_a, f_b, score in pairs:
                print(
                    f"  {f_a.name} <-> {f_b.name}: "
                    f"{score:.4f}"
                )

        # ----------------------------------------
        # STAGE 7 — What the stored embedding looks like
        # ----------------------------------------
        print("\n" + "="*50)
        print("STAGE 7 — What gets stored in the database")
        print("="*50)

        stored = json.dumps(embeddings[0].tolist())
        print(f"JSON string length: {len(stored)} characters")
        print(f"First 100 characters: {stored[:100]}...")
        print(f"\nTo retrieve: json.loads(stored) gives back "
              f"a list of {len(embeddings[0])} floats")
        print(f"Convert to numpy: "
              f"np.array(json.loads(stored))")

    finally:
        db.close()


if __name__ == "__main__":
    main()