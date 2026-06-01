# notes-fastapi/app/services/auth_services/register_service.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User
from app.schemas.user import UserCreateSchema


def create_user(db: Session, payload: UserCreateSchema) -> User:
    # 1. Check if username already exists
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )

    # 2. Check if email already exists
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # 3. Create new user with a securely hashed password
    new_user = User(
        username=payload.username,
        email=payload.email,
        password=security.hash_password(payload.password),
        is_active=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
