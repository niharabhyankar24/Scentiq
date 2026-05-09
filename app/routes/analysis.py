"""
API routes for triggering and retrieving fragrance analysis.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.fragrance import Fragrance
from app.models.ai_insights import AIInsights
from app.tasks import analyse_fragrance_task
from app.utils.dependencies import get_current_user
from app.models.user import User
from celery.result import AsyncResult
from app.worker import celery_app

from slowapi import Limiter
from slowapi.util import get_remote_address
router = APIRouter(tags=["Analysis"])

limiter = Limiter(key_func=get_remote_address)

@router.post("/fragrances/{fragrance_id}/analyse")
@limiter.limit("5/minute")
def trigger_analysis(
    request: Request,
    fragrance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger background AI analysis for a fragrance.
    Returns a job ID immediately for status polling.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    task = analyse_fragrance_task.delay(fragrance_id)
    return {
        "job_id": task.id,
        "status": "started",
        "message": (
            f"Analysis started for "
            f"{fragrance.brand} {fragrance.name}. "
            f"Poll /analysis/status/{task.id} for updates."
        )
    }


@router.get("/analysis/status/{job_id}")
def get_analysis_status(job_id: str):
    """
    Poll the status of a background analysis job.
    Returns current state and result when complete.
    """
    try:
        task_result = AsyncResult(job_id, app=celery_app)
        state = task_result.state

        if state == "PENDING":
            return {
                "job_id": job_id,
                "status": "pending",
                "message": "Job is waiting to start."
            }
        elif state == "PROGRESS":
            return {
                "job_id": job_id,
                "status": "in_progress",
                "message": task_result.info.get(
                    "status", "Processing..."
                ) if task_result.info else "Processing..."
            }
        elif state == "SUCCESS":
            return {
                "job_id": job_id,
                "status": "complete",
                "result": task_result.result
            }
        elif state == "FAILURE":
            return {
                "job_id": job_id,
                "status": "failed",
                "error": "Analysis failed. Please try again."
            }
        else:
            return {
                "job_id": job_id,
                "status": state.lower()
            }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "unknown",
            "message": "Could not retrieve job status."
        }

@router.get(
    "/fragrances/{fragrance_id}/insights",
)
def get_insights(
    fragrance_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored AI insights for a fragrance.
    Returns full insights including perceived notes,
    performance, and value perception.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    insights = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance_id
    ).first()
    if not insights:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No insights found for this fragrance. "
                "Trigger analysis first."
            )
        )
    return {
        "fragrance": {
            "brand": fragrance.brand,
            "name": fragrance.name,
            "concentration": fragrance.concentration
        },
        "insights": json.loads(insights.full_insights),
        "confidence_score": insights.confidence_score,
        "sentiment": insights.sentiment,
        "last_updated": insights.last_updated
    }


@router.get(
    "/fragrances/{fragrance_id}/compare"
)
def compare_official_vs_perceived(
    fragrance_id: int,
    db: Session = Depends(get_db)
):
    """
    Compare official note pyramid against community
    perceived notes side by side. Core value proposition
    of the platform.
    """
    from app.models.note import FragranceNote, PyramidPosition
    from app.models.note import NoteSource

    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )

    def get_notes(position, source):
        """Fetch notes for a given position and source."""
        from app.models.note import Note
        links = db.query(FragranceNote).filter(
            FragranceNote.fragrance_id == fragrance_id,
            FragranceNote.pyramid_position == position,
            FragranceNote.source == source
        ).all()
        note_ids = [link.note_id for link in links]
        notes = db.query(Note).filter(
            Note.id.in_(note_ids)
        ).all()
        return [note.name for note in notes]

    insights = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance_id
    ).first()

    perceived_notes = []
    if insights and insights.full_insights:
        full = json.loads(insights.full_insights)
        perceived_notes = full.get("perceived_notes", [])

    return {
        "fragrance": {
            "brand": fragrance.brand,
            "name": fragrance.name,
            "concentration": fragrance.concentration
        },
        "official_pyramid": {
            "top": get_notes(
                PyramidPosition.top,
                NoteSource.official
            ),
            "heart": get_notes(
                PyramidPosition.heart,
                NoteSource.official
            ),
            "base": get_notes(
                PyramidPosition.base,
                NoteSource.official
            )
        },
        "perceived_notes": perceived_notes,
        "comparison_note": (
            "Official notes reflect the brand's intended "
            "composition. Perceived notes reflect what the "
            "community actually smells and experiences."
        )
    }