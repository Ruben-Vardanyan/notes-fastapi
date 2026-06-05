# notes-fastapi/app/models/note.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)

    title = Column(String(255), nullable=False, index=True)

    text = Column(Text, nullable=False, default="")

    owner_id = Column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Python ORM mappings
    owner = relationship("User", back_populates="owned_notes")

    collaborators = relationship(
        "NoteCollaborator",
        back_populates="note",
        cascade="all, delete-orphan"
    )
