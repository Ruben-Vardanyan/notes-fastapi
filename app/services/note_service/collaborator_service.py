# notes-fastapi/app/services/note_service/collaborator_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.base import Note, NoteCollaborator, User
from app.models.note_collaborator import CollaborationRole


def add_or_update_collaborator(
        db: Session,
        note: Note,
        target_user_id: int,
        role: CollaborationRole
) -> NoteCollaborator:
    """
    Adds a user as a collaborator to a note, or updates their role if they are already added.
    """
    # 1. Prevent owners from adding themselves as a collaborator
    if note.owner_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The owner of the note cannot be added as a collaborator."
        )

    # 2. Verify that the target user actually exists in our system
    user_exists = db.query(User).filter(User.id == target_user_id).first()
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user you are trying to invite does not exist."
        )

    # 3. Look for an existing collaborator record
    collaborator = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note.id,
        NoteCollaborator.user_id == target_user_id
    ).first()

    if collaborator:
        # Update existing role
        collaborator.role = role
    else:
        # Create a new collaborator entry
        collaborator = NoteCollaborator(
            note_id=note.id,
            user_id=target_user_id,
            role=role
        )
        db.add(collaborator)

    db.commit()
    db.refresh(collaborator)

    return collaborator


def remove_collaborator(db: Session, note_id: int, target_user_id: int) -> bool:
    """
    Removes a user from a note's collaborator list. Returns True if deleted.
    """
    deleted_count = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == target_user_id
    ).delete(synchronize_session=False)

    db.commit()

    was_deleted = deleted_count > 0

    if not was_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user is not currently a collaborator on this note."
        )

    return was_deleted
