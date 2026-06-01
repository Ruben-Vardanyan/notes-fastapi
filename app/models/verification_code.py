# notes-fastapi/app/models/verification_code.py
import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.core import timezone
from app.core.database import Base


class VerificationType(str, enum.Enum):
    """Defines what this specific verification token is allowed to do."""
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR = "two_factor"

class VerificationCode(Base):
    __tablename__ = 'verification_codes'

    id = Column(Integer, primary_key=True)

    user_id = Column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    token = Column(String(64), unique=True, nullable=False, index=True)

    purpose = Column(
        Enum(VerificationType),
        nullable=False,
        default=VerificationType.EMAIL_VERIFICATION
    )

    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=timezone.now,
        nullable=False
    )

    user = relationship("User", back_populates="verification_codes")
