# notes-fastapi/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import LoginResponseSchema, LoginSchema, RefreshTokenSchema, RefreshTokenResponseSchema
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.services.auth_services import login_service, register_service, token_service, logout_service

router = APIRouter()


@router.post(
    path='/register',
    response_model=LoginResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def register_user(payload: UserCreateSchema, db: Session = Depends(get_db)):
    """Registers a new user and logs them in instantly by returning tokens."""
    new_user = register_service.create_user(db, payload)

    access_token, refresh_token = token_service.create_tokens(new_user.id)

    return {
        "user": new_user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post(
    path="/login",
    response_model=LoginResponseSchema,
    status_code=status.HTTP_200_OK
)
def login_user(payload: LoginSchema, db: Session = Depends(get_db)):
    """Logs in a user via either their username or email address."""
    user = login_service.login_user(db, payload)

    access_token, refresh_token = token_service.create_tokens(user.id)

    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post(
    path='/refresh',
    response_model=RefreshTokenResponseSchema,
    status_code=status.HTTP_200_OK
)
def refresh_access_token(payload: RefreshTokenSchema, db: Session = Depends(get_db)):
    access_token, refresh_token = token_service.refresh_access_token(db, payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post(
    path='/logout',
    status_code=status.HTTP_200_OK
)
def logout(
        payload: RefreshTokenSchema,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Logs out the authenticated user by invalidating their refresh token.
    Requires a valid Access Token in the Authorization Header.
    """
    logout_service.logout_user(db, user_id=current_user.id, refresh_token=payload.refresh_token)

    return {"detail": f"Successfully logged out user {current_user.username}. Session revoked."}


@router.get("/random", response_model=UserResponseSchema)
def logout(
        current_user: User = Depends(get_current_user)
):
    return current_user
