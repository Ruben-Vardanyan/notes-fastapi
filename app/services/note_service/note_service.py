# notes-fastapi\app\services\note_service\note_service.py
from sqlalchemy.orm import Session
from app.models.base import User
from app.models.note import Note
from app.schemas.note import NoteCreateSchema, NoteUpdateSchema


def create_note(db: Session, payload: NoteCreateSchema, current_user: User):
    db_note = Note(
        title=payload.title,
        text=payload.text,
        owner_id=current_user.id
    )

    db.add(db_note)
    db.commit()

    # Refresh forces SQLAlchemy to fetch server-generated defaults (like id, created_at, updated_at)
    db.refresh(db_note)

    return db_note


def update_note(db: Session, note: Note, payload: NoteUpdateSchema) -> Note:
    """Updates only the fields provided in the payload."""
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(note, key, value)

    db.commit()
    db.refresh(note)
    return note

