# notes-fastapi/app/models/user.py
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean

from app.core import timezone
from app.core.database import Base


class User(Base):
    __tablename__ = 'users'

    # pk
    id = Column(Integer, primary_key=True)

    # required fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # storing hashed passwords
    password = Column(String(255), nullable=False)

    # Optional Fields (nullable=True by default, explicitly stated for clarity)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(Date)

    # Status Flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)

    logged_out_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=timezone.now,
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=timezone.now,
        onupdate=timezone.now,
        nullable=False
    )
