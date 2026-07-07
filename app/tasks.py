"""
Celery tasks for long running background jobs.
"""

from app.worker import celery_app
from app.database import SessionLocal
import app.models.fragrance
import app.models.note
import app.models.user
import app.models.collection
import app.models.ai_insights
import app.models.pricing
import app.models.similarity


@celery_app.task(bind=True, ignore_result=True)
def analyse_fragrance_task(self, fragrance_id: int) -> dict:
    """
    Background task that runs the full AI analysis pipeline
    for a fragrance and generates its embedding.

    Pipeline:
    1. Fetch community content, call Claude, store insights.
    2. Generate a fresh embedding from the updated data.
    3. Advance analysis_refresh_due by refresh_interval_days.
    """
    from datetime import date, timedelta
    from app.models.fragrance import Fragrance
    from app.models.ai_insights import AIInsights

    db = SessionLocal()
    try:
        from app.ai.analyser import analyse_fragrance
        from app.ai.embeddings import generate_embedding

        self.update_state(
            state="PROGRESS",
            meta={"status": "Fetching community content..."}
        )
        insights_result = analyse_fragrance(fragrance_id, db)

        # Generate and save embedding from the fresh data.
        self.update_state(
            state="PROGRESS",
            meta={"status": "Generating embedding..."}
        )
        vector = generate_embedding(db, fragrance_id)
        if vector is not None:
            insights_row = db.query(AIInsights).filter(
                AIInsights.fragrance_id == fragrance_id
            ).first()
            if insights_row:
                insights_row.embedding = vector
                db.commit()

        # Advance the refresh date now that analysis succeeded.
        fragrance = db.query(Fragrance).filter(
            Fragrance.id == fragrance_id
        ).first()
        insights_row = db.query(AIInsights).filter(
            AIInsights.fragrance_id == fragrance_id
        ).first()
        if fragrance and insights_row:
            insights_row.analysis_refresh_due = (
                date.today()
                + timedelta(days=fragrance.refresh_interval_days)
            )
            db.commit()

        return {
            "status": "complete",
            "fragrance_id": fragrance_id,
            "insights": insights_result
        }
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"status": "failed", "error": str(e)}
        )
        raise
    finally:
        db.close()


@celery_app.task(name="scan_and_refresh_due_analyses")
def scan_and_refresh_due_analyses():
    """
    Scan AIInsights for fragrances whose analysis is due
    for refresh, and dispatch analysis tasks for each.

    Runs daily via Celery Beat. The actual analysis runs
    as a separate task per fragrance, queued in the same
    worker pool. This keeps the scanner fast and the
    work parallelisable.

    Returns a count of dispatched tasks for observability.
    """
    from app.models.ai_insights import AIInsights
    from datetime import date

    db = SessionLocal()
    try:
        due = db.query(AIInsights).filter(
            AIInsights.analysis_refresh_due != None,
            AIInsights.analysis_refresh_due <= date.today()
        ).all()

        for insights in due:
            analyse_fragrance_task.delay(insights.fragrance_id)

        return {
            "dispatched": len(due),
            "fragrance_ids": [i.fragrance_id for i in due]
        }
    finally:
        db.close()