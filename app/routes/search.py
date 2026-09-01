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


# ---------------------------------------------------------------
# Occasion / chip search — ranks by the context scores assigned
# during analysis, NOT by embedding similarity. This is what the
# homepage chips use. Each chip maps to one score axis, or to a
# weighted combination of axes.
#
# NULL guard: a fragrance only appears for a chip when every score
# that chip needs is non-NULL. NULL means "not scored yet" (mid-
# analysis, newly added, or a failed run) — distinct from 0.0
# which means "scored, genuinely unsuitable". We never treat an
# unscored fragrance as unsuitable; we simply omit it until it has
# a real judgment. Results are sparser during backfill and fill in
# as analysis completes — fewer-but-correct over more-but-fabricated.
# ---------------------------------------------------------------

# Each chip: the SQL ranking expression, and the list of columns
# that must be non-NULL for a fragrance to qualify. Single-axis
# chips need one column; the combination chip needs all three.
CHIP_DEFINITIONS = {
    "office": {
        "rank": "ai.office_safe",
        "required": ["office_safe"],
    },
    "date": {
        "rank": "ai.date_safe",
        "required": ["date_safe"],
    },
    "cold_weather": {
        "rank": "ai.season_winter",
        "required": ["season_winter"],
    },
    "gym": {
        "rank": "ai.gym_safe",
        "required": ["gym_safe"],
    },
    "formal": {
        "rank": "ai.formal_occasion",
        "required": ["formal_occasion"],
    },
    "daily": {
        "rank": "ai.daily_wear_safe",
        "required": ["daily_wear_safe"],
    },
    # Fresh & clean is not one axis — it's the cluster where a
    # scent is versatile (daily, dominant weight), fresh enough
    # for heat (summer), and clean enough for the gym. Daily is
    # weighted highest so elegant-versatile scents (e.g. BdC)
    # win over pure sport-aquatics that only ace the gym.
    "fresh_clean": {
        "rank": (
            "(0.5 * ai.daily_wear_safe"
            " + 0.3 * ai.season_summer"
            " + 0.2 * ai.gym_safe)"
        ),
        "required": ["daily_wear_safe", "season_summer", "gym_safe"],
    },
}

# Only surface fragrances whose ranking score clears this bar,
# so a chip never returns fragrances that are merely "least bad".
CHIP_SCORE_FLOOR = 0.5


class OccasionSearchRequest(BaseModel):
    chip: str


@router.post("/occasion")
def occasion_search(
    payload: OccasionSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Rank fragrances for a homepage chip by their context scores.

    Unlike semantic search, this doesn't embed anything — it sorts
    by the 0-1 judgment scores assigned during analysis. Each chip
    maps to one axis or a weighted blend (see CHIP_DEFINITIONS).

    Consent-gated logging mirrors semantic search: a logged-in,
    consenting user's chip selection is recorded to search_queries
    (stored as "chip:<name>" so it's distinguishable from typed
    queries). Anonymous or non-consenting users log nothing.
    """
    chip = payload.chip.strip()
    definition = CHIP_DEFINITIONS.get(chip)
    if definition is None:
        return {"chip": chip, "results": [], "count": 0}

    # Consent-gated logging, same rule as semantic search.
    if current_user and current_user.consent_search_history:
        db.add(SearchQuery(
            user_id=current_user.id,
            query=f"chip:{chip}",
        ))
        db.commit()

    # Build the NULL guard: every required score must be present.
    null_guard = " AND ".join(
        f"ai.{col} IS NOT NULL" for col in definition["required"]
    )
    rank_expr = definition["rank"]

    # Note: rank_expr and null_guard are built only from the
    # hardcoded CHIP_DEFINITIONS above — never from user input —
    # so there's no injection surface despite the string build.
    sql = text(f"""
        SELECT
            ai.fragrance_id,
            {rank_expr} AS score
        FROM ai_insights ai
        WHERE {null_guard}
          AND {rank_expr} >= :floor
        ORDER BY {rank_expr} DESC
        LIMIT 10
    """)

    rows = db.execute(sql, {"floor": CHIP_SCORE_FLOOR}).fetchall()

    results = []
    for row in rows:
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
            "score": round(float(row.score), 3),
        })

    return {
        "chip": chip,
        "results": results,
        "count": len(results),
    }