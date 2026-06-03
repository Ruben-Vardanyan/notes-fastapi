# notes-fastapi/app/schemas/note.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.note_collaborator import CollaboratorResponseSchema
from app.schemas.user import UserSmallSchema


class NoteCreateSchema(BaseModel):
    """Payload required to instantiate a brand-new note entry."""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the note.")
    text: str = Field(default="", description="The markdown body or content of the note.")


class NoteUpdateSchema(BaseModel):
    """Payload required to edit an existing note's metadata or core body."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    text: str | None = Field(default=None)


class NoteResponseSchema(BaseModel):
    """The clean outward-facing representation of a complete Note object."""
    id: int
    title: str
    text: str
    owner: UserSmallSchema
    created_at: datetime
    updated_at: datetime

    # Nests the collaborator information cleanly for the frontend engine
    collaborators: list[CollaboratorResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)
