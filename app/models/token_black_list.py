# notes-fastapi/app/models/token_black_list.py
from sqlalchemy import Column, Integer, String, DateTime

from app.core import timezone
from app.core.database import Base


class TokenBlackList(Base):
    __tablename__ = "token_black_list"

    # pk
    id = Column(Integer, primary_key=True)

    # expired refresh jwt token
    refresh_token = Column(String(512), nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=timezone.now,
        nullable=False
    )
