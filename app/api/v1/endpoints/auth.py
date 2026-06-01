# notes-fastapi/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from app.core.database import get_db
from app.core.limiter import limiter
from app.dependencies.auth import get_current_user, get_current_inactive_user
from app.models.user import User
from app.schemas.auth import LoginResponseSchema, LoginSchema, RefreshTokenSchema, RefreshTokenResponseSchema
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.services.auth_services import login_service, register_service, token_service, logout_service, email_service

router = APIRouter()


@router.post(
    path='/register',
    response_model=LoginResponseSchema,
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register_user(
        request: Request,
        payload: UserCreateSchema,
        db: Session = Depends(get_db)
):
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
@limiter.limit("5/minute")
def login_user(
        request: Request,
        payload: LoginSchema,
        db: Session = Depends(get_db)
):
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
@limiter.limit("30/minute")
def refresh_access_token(
        request: Request,
        payload: RefreshTokenSchema,
        db: Session = Depends(get_db)
):
    access_token, refresh_token = token_service.refresh_access_token(db, payload)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post(
    path='/logout',
    status_code=status.HTTP_200_OK
)
@limiter.limit("10/minute")
def logout(
        request: Request,
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


@router.post(
    path='/request-verification',
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")
def request_verification_email(
        request: Request,
        background_tasks: BackgroundTasks,  # ◄─ Triggers non-blocking background jobs
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_inactive_user)
):
    email_service.create_and_send_verification(db, current_user, background_tasks)
    return {"detail": "Verification email dispatched successfully."}


@router.get(
    path='/verify-email/{token}'
)
@limiter.limit("10/minute")
def verify_email(
    request: Request,
    token: str,
    db: Session = Depends(get_db)
):
    email_service.execute_email_verification(db, token)

    test_redirect_url = "https://google.com"
    return RedirectResponse(url=test_redirect_url, status_code=status.HTTP_303_SEE_OTHER)
