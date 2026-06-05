# notes-fastapi/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from app.core.database import get_db
from app.core.limiter import limiter
from app.dependencies.auth import get_current_user, get_current_inactive_user
from app.models.user import User
from app.schemas.auth import LoginResponseSchema, LoginSchema, RefreshTokenSchema, RefreshTokenResponseSchema, \
    ForgotPasswordSchema, ResetPasswordSchema
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.services.auth_services import login_service, register_service, token_service, logout_service, email_service, \
    email_verification_service, forgot_password_service, reset_password_service

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
    """Refreshes a new token pair and blacklists the old refresh token."""
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
    Logs out the authenticated user by blacklisting their refresh token.
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
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_inactive_user)
):
    """Sends email with verification link."""
    email_verification_service.create_and_send_verification(db, current_user, background_tasks)
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
    """Verifies user by making user active"""
    email_verification_service.execute_email_verification(db, token)

    test_redirect_url = "https://google.com"
    return RedirectResponse(url=test_redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post(
    path="/forgot-password",
    status_code=status.HTTP_200_OK
)
@limiter.limit("3/minute")
def forgot_password(
        request: Request,
        payload: ForgotPasswordSchema,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """
    Sends an email to user with a link for reset password.
    """
    forgot_password_service.process_forgot_password(db, payload.email, background_tasks)

    return {
        "detail": "If an account matches that email address, a password reset link has been dispatched."
    }

@router.post(
    path='/reset-password',
    status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")  # Prevent brute forcing or spamming password inputs
def reset_password(
        request: Request,
        payload: ResetPasswordSchema,
        db: Session = Depends(get_db)
):
    """
    Resets user's password.
    """
    reset_password_service.execute_password_reset(db, payload.token, payload.new_password)

    return {"detail": "Password has been successfully updated. Please log in with your new credentials."}
