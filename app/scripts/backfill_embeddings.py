"""
One-off script to backfill embeddings for all fragrances.

Run once after enabling pgvector to embed the entire
catalogue. Idempotent — re-running is safe, overwrites
existing embeddings with fresh ones.

Usage: python -m app.scripts.backfill_embeddings
"""

from app.database import SessionLocal
import app.models.fragrance
import app.models.note
import app.models.user
import app.models.collection
import app.models.ai_insights
import app.models.pricing
import app.models.similarity

from app.models.fragrance import Fragrance
from app.models.ai_insights import AIInsights
from app.ai.embeddings import generate_embedding


def backfill():
    db = SessionLocal()
    try:
        fragrances = db.query(Fragrance).all()
        total = len(fragrances)
        print(f"Backfilling embeddings for {total} fragrances...")

        succeeded = 0
        skipped = 0

        for i, fragrance in enumerate(fragrances, 1):
            print(
                f"[{i}/{total}] {fragrance.brand} "
                f"{fragrance.name} (id={fragrance.id})...",
                flush=True
            )

            vector = generate_embedding(db, fragrance.id)
            if vector is None:
                print("  skipped (no fragrance loaded)")
                skipped += 1
                continue

            insights_row = db.query(AIInsights).filter(
                AIInsights.fragrance_id == fragrance.id
            ).first()

            # If no AIInsights row exists yet, create one so we
            # have somewhere to store the embedding.
            if not insights_row:
                insights_row = AIInsights(
                    fragrance_id=fragrance.id
                )
                db.add(insights_row)

            insights_row.embedding = vector
            db.commit()
            succeeded += 1
            print("  done")

        print(
            f"\nBackfill complete: "
            f"{succeeded} succeeded, {skipped} skipped."
        )
    finally:
        db.close()


if __name__ == "__main__":
    backfill()