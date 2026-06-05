# notes-fastapi/app/api/v1/endpoints/notes.py
from typing import Literal

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.core.limiter import limiter
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.base import User, Note
from app.schemas.note import NoteCreateSchema, NoteResponseSchema, NoteUpdateSchema
from app.schemas.note_collaborator import CollaboratorAddSchema, CollaboratorResponseSchema
from app.services.note_service import note_service, collaborator_service
from app.services.note_service.general_note_services import get_note_by_id, get_note_with_read_permission, \
    get_note_with_write_permission
from app.services.note_service.note_filter_service import get_user_notes_feed

router = APIRouter()


@router.get(
    "/",
    response_model=list[NoteResponseSchema],
    summary="List notes with multi-option filters",
)
@limiter.limit("60/minute")
def list_notes(
        request: Request,
        search: str | None = Query(default=None, description="Search term matching title or body content."),
        filter_by: list[Literal["owned", "editor", "viewer"]] = Query(
            default=["owned", "editor", "viewer"],
            description="Filter results by one or more permission levels. Defaults to everything."
        ),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Returns a searchable feed of notes matching any of the selected filter criteria.
    """
    return get_user_notes_feed(db, user_obj=current_user, search=search, filters=filter_by)


@router.get(
    "/{note_id}",
    response_model=NoteResponseSchema,
    summary="Get a specific note by ID",
)
@limiter.limit("60/minute")
def read_note(
        request: Request,
        note_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Accessible by the absolute owner or any invited collaborator (Editor/Viewer)."""
    return get_note_with_read_permission(db, note_id=note_id, user=current_user)


@router.post(
    "/",
    response_model=NoteResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
)
@limiter.limit("100/minute")
def create_note(
        request: Request,
        payload: NoteCreateSchema,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    new_note = note_service.create_note(db, payload, current_user)

    return new_note


@router.patch(
    "/{note_id}",
    response_model=NoteResponseSchema,
    summary="Update a note's content",
)
@limiter.limit("40/minute")
def edit_note(
        request: Request,
        note_id: int,
        payload: NoteUpdateSchema,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    note = get_note_with_write_permission(db, note_id=note_id, user=current_user)

    return note_service.update_note(db, note=note, payload=payload)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
)
@limiter.limit("20/minute")
def delete_note(
        request: Request,
        note_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Permanently deletes a note. Only the absolute owner is authorized to do this.
    """
    note = get_note_by_id(db, note_id=note_id, owner=current_user)
    # SQLAlchemy cascades will auto-purge collaborator records
    db.delete(note)
    db.commit()

    return None


@router.put(
    "/{note_id}/collaborators",
    response_model=CollaboratorResponseSchema,
    summary="Add or update a collaborator",
)
@limiter.limit("30/minute")
def add_or_update_note_collaborator(
        request: Request,
        note_id: int,
        payload: CollaboratorAddSchema,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Allows the note owner to invite a new collaborator or modify an existing collaborator's role.
    """
    note = get_note_by_id(db, note_id=note_id, owner=current_user)

    return collaborator_service.add_or_update_collaborator(
        db=db,
        note=note,
        target_user_id=payload.user_id,
        role=payload.role
    )


@router.delete(
    "/{note_id}/collaborators/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a collaborator",
)
@limiter.limit("30/minute")
def remove_note_collaborator(
        request: Request,
        note_id: int,
        user_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Allows the note owner to revoke a collaborator's access to a note.
    """
    # Verifies ownership authority first
    get_note_by_id(db, note_id=note_id, owner=current_user)
    collaborator_service.remove_collaborator(db=db, note_id=note_id, target_user_id=user_id)

    return None
