"""
Semantic search endpoint.

Uses sentence transformer embeddings and pgvector cosine
similarity to find fragrances by natural language queries.

The endpoint is public — anonymous users search normally.
When a valid token is present AND the user has enabled
consent_search_history, the query is logged into
search_queries. This is the ONLY place in the codebase
that writes to search_queries in normal operation.
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models.fragrance import Fragrance
from app.models.ai_insights import AIInsights
from app.models.user import User
from app.models.search_query import SearchQuery
from app.ai.embeddings import get_model
from app.utils.dependencies import get_optional_user


router = APIRouter()


class SemanticSearchRequest(BaseModel):
    query: str


# Minimum similarity threshold — results below this are
# excluded because they don't meaningfully match the query.
SIMILARITY_THRESHOLD = 0.3


@router.post("/semantic")
def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search fragrances by natural language query.

    Embeds the query using the same sentence transformer
    model as the fragrances, then runs a pgvector cosine
    similarity search. Returns top matches with match scores.

    Consent-gated logging: if the request carries a valid
    token AND that user has consent_search_history == True,
    the query text is written to search_queries. Anonymous
    requests and non-consenting users never write a row.
    """
    query_text = payload.query.strip()
    if not query_text:
        return {"query": "", "results": [], "count": 0}

    # Consent-gated history logging.
    # Guarded by both authentication AND explicit consent.
    if current_user and current_user.consent_search_history:
        db.add(SearchQuery(
            user_id=current_user.id,
            query=query_text
        ))
        db.commit()

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