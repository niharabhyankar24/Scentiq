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

@celery_app.task(bind=True)
def analyse_fragrance_task(self, fragrance_id: int) -> dict:
    """
    Background task that runs the full AI analysis pipeline
    for a fragrance. Returns structured insights on completion.
    """
    db = SessionLocal()
    try:
        from app.ai.analyser import analyse_fragrance
        self.update_state(
            state="PROGRESS",
            meta={"status": "Fetching community content..."}
        )
        insights = analyse_fragrance(fragrance_id, db)
        return {
            "status": "complete",
            "fragrance_id": fragrance_id,
            "insights": insights
        }
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={"status": "failed", "error": str(e)}
        )
        raise
    finally:
        db.close()