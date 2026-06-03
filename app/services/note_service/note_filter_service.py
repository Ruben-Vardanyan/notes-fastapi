# notes-fastapi\app\services\note_service\note_filter_service.py
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from app.models.base import Note, NoteCollaborator, User
from app.models.note_collaborator import CollaborationRole


def get_user_notes_feed(
        db: Session,
        user_obj: "User",
        search: str | None = None,
        filters: list[str] = None
) -> list[Note]:
    """
    Fetches notes using a dynamic array of filters (e.g., ['editor', 'viewer']).
    """
    if filters is None:
        filters = ["owned", "editor", "viewer"]

    query = db.query(Note).outerjoin(NoteCollaborator)

    # This array will hold the SQL conditions that match the user's choices
    conditions = []

    if "owned" in filters:
        conditions.append(Note.owner_id == user_obj.id)

    if "editor" in filters:
        conditions.append(
            and_(
                NoteCollaborator.user_id == user_obj.id,
                NoteCollaborator.role == CollaborationRole.EDITOR
            )
        )

    if "viewer" in filters:
        conditions.append(
            and_(
                NoteCollaborator.user_id == user_obj.id,
                NoteCollaborator.role == CollaborationRole.VIEWER
            )
        )

    # 1. Apply the accumulated security conditions under an OR wrapper
    if conditions:
        query = query.filter(or_(*conditions))
    else:
        # Edge case: If the user explicitly passed an empty filter list `?filter_by=`,
        # prevent leaking data by forcing a condition that returns nothing.
        query = query.filter(Note.id == -1)

    # 2. Handle Text Searching
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Note.title.ilike(search_term),
                Note.text.ilike(search_term)
            )
        )

    return query.distinct().order_by(Note.updated_at.desc()).all()
