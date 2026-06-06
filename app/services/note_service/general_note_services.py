# notes-fastapi\app\services\note_service\general_note_services.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.base import Note, User
from app.models.note_collaborator import NoteCollaborator, CollaborationRole


def get_note_by_id(db: Session, note_id: int, owner: User = None):
    query = db.query(Note).filter(Note.id == note_id)

    if owner is not None:
        query = query.filter(Note.owner_id == owner.id)

    note = query.first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or access denied."
        )

    return note


def get_note_with_read_permission(db: Session, note_id: int, user: User) -> Note:
    """
    Fetches a note if the user is the owner OR a registered collaborator (Editor/Viewer).
    Throws a 404 if the note doesn't exist, or 403 if they don't have access.
    """
    # 1. Check if the note exists at all globally
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    # 2. If they are the owner, they are good to go!
    if note.owner_id == user.id:
        return note

    # 3. Check if they are a collaborator
    is_collaborator = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == user.id
    ).first()

    if not is_collaborator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this note."
        )

    return note


def get_note_with_write_permission(db: Session, note_id: int, user: User) -> Note:
    """
    Fetches a note only if the user is the owner OR an explicit EDITOR.
    Viewers will be blocked here.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")

    if note.owner_id == user.id:
        return note

    # Check if they have an active EDITOR tier assignment
    has_edit_rights = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == user.id,
        NoteCollaborator.role == CollaborationRole.EDITOR
    ).first()

    if not has_edit_rights:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have editing privileges for this note."
        )

    return note
