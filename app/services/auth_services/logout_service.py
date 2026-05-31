# notes-fastapi/app/services/auth_services/logout_service.py
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core import security
from app.models.user import User
from app.services.auth_services.token_service import is_blacklisted, blacklist_refresh_token


def logout_user(db: Session, user_id: int, refresh_token: str) -> None:
    """
    Logs out a user globally by setting their logout timestamp
    and blacklisting their refresh token.
    """
    # 1. Decode and strictly validate the refresh token FIRST
    token_data = security.decode_jwt_token(refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type sent for logout. A refresh token is required."
        )

    exp_timestamp = token_data.get("exp")
    if exp_timestamp is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token. Missing expiration claim."
        )

    # 2. Update the user's global logout timestamp
    db.query(User).filter(User.id == user_id).update(
        {User.logged_out_at: datetime.now(timezone.utc)}
    )

    # 3. Securely blacklist the refresh token if it hasn't been burned yet
    if not is_blacklisted(db, refresh_token):
        blacklist_refresh_token(
            db=db,
            token=refresh_token,
            expires_at_timestamp=exp_timestamp
        )

    # 4. Commit all updates together safely
    db.commit()
