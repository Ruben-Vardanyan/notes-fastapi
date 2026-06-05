# notes-fastapi/app/schemas/note.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.note_collaborator import CollaboratorResponseSchema
from app.schemas.user import UserSmallSchema


class NoteCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the note.")
    text: str = Field(default="", description="The markdown body or content of the note.")


class NoteUpdateSchema(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    text: str | None = Field(default=None)


class NoteResponseSchema(BaseModel):
    id: int
    title: str
    text: str
    owner: UserSmallSchema
    created_at: datetime
    updated_at: datetime

    collaborators: list[CollaboratorResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)
