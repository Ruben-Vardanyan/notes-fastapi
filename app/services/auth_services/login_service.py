# notes-fastapi\app\services\auth_services\login_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core import security
from app.models.user import User
from app.schemas.auth import LoginSchema


def login_user(db: Session, payload: LoginSchema) -> User | None:
    user = db.query(User).filter(
        (User.email == payload.identifier) | (User.username == payload.identifier)
    ).first()

    # 2. Safety check: Verify existence and evaluate password hash
    if not user or not security.verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is not active"
        )

    return user
