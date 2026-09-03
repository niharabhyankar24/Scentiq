from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.note import Note, FragranceNote
from app.models.fragrance import Fragrance
from app.schemas.note import (
    NoteCreate, NoteResponse,
    FragranceNoteCreate, FragranceNoteResponse
)

router = APIRouter(tags=["Notes"])



@router.get(
    "/notes",
    response_model=list[NoteResponse]
)
def get_notes(db: Session = Depends(get_db)):
    """Return all scent notes in the database."""
    return db.query(Note).all()


@router.get(
    "/notes/{note_id}",
    response_model=NoteResponse
)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Return a single scent note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note



@router.get(
    "/fragrances/{fragrance_id}/notes",
    response_model=list[FragranceNoteResponse]
)
def get_fragrance_notes(
    fragrance_id: int,
    db: Session = Depends(get_db)
):
    """Return all notes linked to a specific fragrance."""
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    return db.query(FragranceNote).filter(
        FragranceNote.fragrance_id == fragrance_id
    ).all()