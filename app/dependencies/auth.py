# notes-fastapi/app/dependencies/auth.py
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def get_current_user(
        token: str | None = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = security.decode_jwt_token(token)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    issued_at_timestamp = payload.get("iat")

    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. An access token is required."
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )

    # GRACE PERIOD CHECK: Compare token birth vs user logout timestamp
    if user.logged_out_at and issued_at_timestamp:
        token_issued_at = datetime.fromtimestamp(issued_at_timestamp, tz=timezone.utc)

        if token_issued_at < user.logged_out_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked by a recent logout event. Please log in again."
            )

    return user


def get_current_active_superuser(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to restrict a route exclusively to Admin/Superusers.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have administrative privileges to perform this action"
        )
    return current_user
