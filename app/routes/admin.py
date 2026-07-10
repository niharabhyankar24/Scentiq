"""
Admin-only routes for managing the fragrance catalogue.

All routes in this module require the requester to be
authenticated AND have is_admin=True. Access is enforced
via the get_admin_user dependency on every endpoint.
"""

from fastapi import APIRouter, Depends

from app.models.user import User
from app.utils.dependencies import get_admin_user
from datetime import date, timedelta
from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.models.fragrance import Fragrance
from app.models.ai_insights import AIInsights
from app.schemas.fragrance import (
    FragranceCreate, FragranceResponse,
    AdminNoteAssignment, AdminNoteUpdate
)

from app.models.note import (
    Note, FragranceNote,
    PyramidPosition, NoteSource, IntensityLevel
)

from sqlalchemy.exc import IntegrityError
from app.models.note import Note, FragranceNote, PyramidPosition, NoteSource
from app.schemas.fragrance import AdminNoteAssignment

router = APIRouter()


@router.get("/ping")
def admin_ping(
    current_user: User = Depends(get_admin_user)
):
    """
    Health check for admin authentication.

    Returns a simple confirmation if the requester is
    a valid admin. Useful for the frontend to verify
    admin status before rendering the admin panel.
    """
    return {
        "ok": True,
        "admin_email": current_user.email
    }
    
@router.post(
    "/fragrances",
    response_model=FragranceResponse,
    status_code=201
)
def admin_create_fragrance(
    payload: FragranceCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new fragrance in the catalogue and queue
    its AI analysis.

    Creates the Fragrance row, an empty AIInsights row
    with a future analysis_refresh_due date, and
    dispatches the Celery analysis task. Returns the
    created fragrance immediately; analysis completes
    asynchronously.
    """
    # 1. Create the fragrance.
    fragrance = Fragrance(
        **payload.model_dump(),
    )
    db.add(fragrance)
    db.commit()
    db.refresh(fragrance)

    # 2. Create the empty AIInsights row to track refresh.
    insights = AIInsights(
        fragrance_id=fragrance.id,
        analysis_refresh_due=date.today() + timedelta(
            days=payload.refresh_interval_days
        )
    )
    db.add(insights)
    db.commit()

    # 3. Queue the Celery analysis task.
    # Lazy import keeps startup fast.
    from app.tasks import analyse_fragrance_task
    analyse_fragrance_task.delay(fragrance.id)

    return fragrance

@router.post("/fragrances/{fragrance_id}/notes", status_code=201)
def admin_assign_note(
    fragrance_id: int,
    payload: AdminNoteAssignment,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Assign a note to a fragrance at a pyramid position.

    Accepts either an existing note_id or a new note_name
    (with note_category) to create. Returns the resulting
    FragranceNote row. Idempotent — calling twice with the
    same arguments returns the existing assignment.
    """
    # Verify the fragrance exists.
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(404, "Fragrance not found")

    # Resolve or create the note.
    if payload.note_id:
        note = db.query(Note).filter(
            Note.id == payload.note_id
        ).first()
        if not note:
            raise HTTPException(404, "Note not found")
    else:
        # Find existing by name (case-insensitive) or create.
        note = db.query(Note).filter(
            Note.name.ilike(payload.note_name)
        ).first()
        if not note:
            # Convert string intensity to enum if provided.
            intensity_enum = None
            if payload.note_intensity:
                intensity_enum = IntensityLevel(payload.note_intensity)

            note = Note(
                name=payload.note_name,
                category=payload.note_category,
                description=payload.note_description,
                polarizing=payload.note_polarizing,
                intensity=intensity_enum
            )
            db.add(note)
            db.commit()
            db.refresh(note)
    # Attach to fragrance with idempotent insert.
    try:
        link = FragranceNote(
            fragrance_id=fragrance_id,
            note_id=note.id,
            pyramid_position=PyramidPosition(
                payload.pyramid_position
            ),
            source=NoteSource.official
        )
        db.add(link)
        db.commit()
        db.refresh(link)
    except IntegrityError:
        # Already exists — fetch the existing row.
        db.rollback()
        link = db.query(FragranceNote).filter(
            FragranceNote.fragrance_id == fragrance_id,
            FragranceNote.note_id == note.id,
            FragranceNote.source == NoteSource.official
        ).first()

    return {
        "id": link.id,
        "fragrance_id": link.fragrance_id,
        "note_id": link.note_id,
        "note_name": note.name,
        "pyramid_position": link.pyramid_position.value,
        "source": link.source.value
    }
    
@router.patch("/notes/{note_id}")
def admin_update_note(
    note_id: int,
    payload: AdminNoteUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update fields on a Note. Only fields provided in the
    payload are modified; omitted fields are left as-is.

    Affects every fragrance that uses this note, since
    Note properties (description, polarizing, intensity)
    are global to the note itself.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(404, "Note not found")

    # Apply only fields the admin explicitly provided.
    update_data = payload.model_dump(exclude_unset=True)

    if "intensity" in update_data:
        # Convert string to enum.
        update_data["intensity"] = (
            IntensityLevel(update_data["intensity"])
            if update_data["intensity"] else None
        )

    for field, value in update_data.items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)

    return {
        "id": note.id,
        "name": note.name,
        "category": note.category,
        "description": note.description,
        "polarizing": note.polarizing,
        "intensity": (
            note.intensity.value if note.intensity else None
        )
    }

@router.delete(
    "/fragrances/{fragrance_id}/notes/{note_id}",
    status_code=204
)
def admin_remove_note(
    fragrance_id: int,
    note_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Remove an officially-assigned note from a fragrance.

    Only removes assignments where source='official'.
    AI-generated perceived notes are left untouched —
    those should be corrected by re-running analysis.
    """
    link = db.query(FragranceNote).filter(
        FragranceNote.fragrance_id == fragrance_id,
        FragranceNote.note_id == note_id,
        FragranceNote.source == NoteSource.official
    ).first()

    if not link:
        raise HTTPException(
            404,
            "Note assignment not found"
        )

    db.delete(link)
    db.commit()
    return None

@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Return catalogue stats and per-fragrance analysis
    status for the admin dashboard.

    Status is derived from AIInsights row state:
    - complete: row exists with snapshot_draft populated
    - pending: row exists but snapshot_draft is NULL
    - missing: no AIInsights row at all
    """
    fragrances = db.query(Fragrance).options(
        joinedload(Fragrance.insights)
    ).order_by(Fragrance.id.desc()).all()

    items = []
    counts = {"complete": 0, "pending": 0, "missing": 0}

    for f in fragrances:
        insights = f.insights
        if not insights:
            status = "missing"
        elif insights.snapshot_draft:
            status = "complete"
        else:
            status = "pending"

        counts[status] += 1

        items.append({
            "id": f.id,
            "brand": f.brand,
            "name": f.name,
            "analysis_status": status,
            "analysis_refresh_due": (
                insights.analysis_refresh_due.isoformat()
                if insights and insights.analysis_refresh_due
                else None
            ),
            "refresh_interval_days": f.refresh_interval_days
        })

    return {
        "stats": {
            "total_fragrances": len(fragrances),
            "analyzed": counts["complete"],
            "pending": counts["pending"],
            "missing_insights": counts["missing"]
        },
        "fragrances": items
    }

@router.post("/fragrances/{fragrance_id}/refresh-analysis")
def admin_refresh_analysis(
    fragrance_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Manually queue an AI analysis refresh for a fragrance.

    Updates analysis_refresh_due forward by the fragrance's
    refresh_interval_days, then dispatches the Celery task.
    The endpoint returns immediately; analysis completes
    asynchronously in the worker.
    """
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(404, "Fragrance not found")

    # Ensure an AIInsights row exists. Defensive — Step 7
    # always creates one, but a fragrance could theoretically
    # exist without one (e.g. seeded before V2).
    insights = db.query(AIInsights).filter(
        AIInsights.fragrance_id == fragrance_id
    ).first()
    if not insights:
        insights = AIInsights(fragrance_id=fragrance_id)
        db.add(insights)

    # Push the next refresh date forward.
    insights.analysis_refresh_due = date.today() + timedelta(
        days=fragrance.refresh_interval_days
    )
    db.commit()

    # Queue the task.
    from app.tasks import analyse_fragrance_task
    task = analyse_fragrance_task.delay(fragrance_id)

    return {
        "queued": True,
        "task_id": task.id,
        "fragrance_id": fragrance_id,
        "next_refresh_due": insights.analysis_refresh_due.isoformat()
    }

@router.post("/backfill-embeddings")
def admin_backfill_embeddings(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    One-off backfill of embeddings for every fragrance.

    Generates fresh embeddings from existing analysis data
    without re-running the AI pipeline. Idempotent — safe
    to call multiple times. Meant to be removed after the
    initial run.
    """
    from app.ai.embeddings import generate_embedding
    from app.models.ai_insights import AIInsights

    fragrances = db.query(Fragrance).all()
    succeeded = 0
    skipped = 0
    failed = []

    for fragrance in fragrances:
        try:
            vector = generate_embedding(db, fragrance.id)
            if vector is None:
                skipped += 1
                continue

            insights_row = db.query(AIInsights).filter(
                AIInsights.fragrance_id == fragrance.id
            ).first()
            if not insights_row:
                insights_row = AIInsights(
                    fragrance_id=fragrance.id
                )
                db.add(insights_row)

            insights_row.embedding = vector
            db.commit()
            succeeded += 1
        except Exception as e:
            failed.append({
                "fragrance_id": fragrance.id,
                "error": str(e)
            })

    return {
        "total": len(fragrances),
        "succeeded": succeeded,
        "skipped": skipped,
        "failed": failed
    }