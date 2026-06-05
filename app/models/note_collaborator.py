# notes-fastapi/app/models/note_collaborator.py
import enum
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CollaborationRole(str, enum.Enum):
    """Defines the specific access capabilities a shared user has over a note."""
    EDITOR = "editor"
    VIEWER = "viewer"


class NoteCollaborator(Base):
    __tablename__ = "note_collaborators"

    id = Column(Integer, primary_key=True)

    # Cascade ensures if the parent note is deleted, its sharing records are swept away automatically
    note_id = Column(
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role = Column(
        Enum(CollaborationRole),
        nullable=False,
        default=CollaborationRole.VIEWER
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships to navigate back and forth in Python code
    note = relationship("Note", back_populates="collaborators")
    user = relationship("User")

    # CRITICAL SECURITY CONSTRAINT: A user can only be added to a note once!
    __table_args__ = (
        UniqueConstraint("note_id", "user_id", name="uq_note_user_collaboration"),
    )