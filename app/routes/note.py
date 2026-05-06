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


@router.post(
    "/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED
)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    """Create a new scent note in the database."""
    existing = db.query(Note).filter(
        Note.name == note.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A note with this name already exists"
        )
    db_note = Note(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


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


@router.post(
    "/fragrances/{fragrance_id}/notes",
    response_model=FragranceNoteResponse,
    status_code=status.HTTP_201_CREATED
)
def add_note_to_fragrance(
    fragrance_id: int,
    note_data: FragranceNoteCreate,
    db: Session = Depends(get_db)
):
    """Link an existing note to a fragrance with position and source."""
    fragrance = db.query(Fragrance).filter(
        Fragrance.id == fragrance_id
    ).first()
    if not fragrance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fragrance not found"
        )
    note = db.query(Note).filter(
        Note.id == note_data.note_id
    ).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    db_fragrance_note = FragranceNote(
        fragrance_id=fragrance_id,
        **note_data.model_dump()
    )
    db.add(db_fragrance_note)
    db.commit()
    db.refresh(db_fragrance_note)
    return db_fragrance_note


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