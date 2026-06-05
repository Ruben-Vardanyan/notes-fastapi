# notes-fastapi/app/schemas/note_collaborator.py
from pydantic import BaseModel, ConfigDict, Field
from app.models.note_collaborator import CollaborationRole
from app.schemas.user import UserSmallSchema


class CollaboratorAddSchema(BaseModel):
    user_id: int
    role: CollaborationRole = Field(
        default=CollaborationRole.VIEWER,
        description="The access tier assigned to this user ('editor' or 'viewer')."
    )


class CollaboratorResponseSchema(BaseModel):
    user: UserSmallSchema
    role: CollaborationRole

    model_config = ConfigDict(from_attributes=True)
