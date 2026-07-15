"""
Semantic search endpoint.

Uses sentence transformer embeddings and pgvector cosine
similarity to find fragrances by natural language queries.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.fragrance import Fragrance
from app.models.ai_insights import AIInsights
from app.ai.embeddings import get_model


router = APIRouter()


class SemanticSearchRequest(BaseModel):
    query: str


# Minimum similarity threshold — results below this are
# excluded because they don't meaningfully match the query.
SIMILARITY_THRESHOLD = 0.5


@router.post("/semantic")
def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search fragrances by natural language query.

    Embeds the query using the same sentence transformer
    model as the fragrances, then runs a pgvector cosine
    similarity search. Returns top matches with match scores.
    """
    query_text = payload.query.strip()
    if not query_text:
        return {"query": "", "results": [], "count": 0}

    # Embed the query into the same vector space as fragrances.
    model = get_model()
    query_vector = model.encode(
        query_text, convert_to_numpy=True
    ).tolist()

    # Cosine similarity query via pgvector's <=> operator.
    # 1 - distance gives similarity in ~[0, 1] range.
    sql = text("""
        SELECT
            ai.fragrance_id,
            1 - (ai.embedding <=> CAST(:query_vec AS vector))
                AS similarity
        FROM ai_insights ai
        WHERE ai.embedding IS NOT NULL
        ORDER BY ai.embedding <=> CAST(:query_vec AS vector)
        LIMIT 20
    """)

    rows = db.execute(
        sql,
        {"query_vec": str(query_vector)}
    ).fetchall()

    # Filter by threshold and load fragrance metadata.
    results = []
    for row in rows:
        similarity = float(row.similarity)
        if similarity < SIMILARITY_THRESHOLD:
            continue

        fragrance = db.query(Fragrance).filter(
            Fragrance.id == row.fragrance_id
        ).first()
        if not fragrance:
            continue

        results.append({
            "id": fragrance.id,
            "brand": fragrance.brand,
            "name": fragrance.name,
            "concentration": fragrance.concentration,
            "scent_family_name": (
                fragrance.scent_family.name
                if fragrance.scent_family else None
            ),
            "image_url": fragrance.image_url,
            "similarity": round(similarity, 3)
        })

        if len(results) >= 10:
            break

    return {
        "query": query_text,
        "results": results,
        "count": len(results)
    }