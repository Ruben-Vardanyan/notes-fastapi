# notes-fastapi/app/schemas/note_collaborator.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.note_collaborator import CollaborationRole
from app.schemas.user import UserSmallSchema


class CollaboratorAddSchema(BaseModel):
    """Payload required to share a note with another user."""
    user_id: int
    role: CollaborationRole = Field(
        default=CollaborationRole.VIEWER,
        description="The access tier assigned to this user ('editor' or 'viewer')."
    )


class CollaboratorResponseSchema(BaseModel):
    """Public representation of a collaborator attached to a note."""
    user: UserSmallSchema
    role: CollaborationRole

    model_config = ConfigDict(from_attributes=True)
