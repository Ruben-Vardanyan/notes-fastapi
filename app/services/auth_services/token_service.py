# notes-fastapi/app/services/auth_services/token_service.py
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.core import security
from app.core.config import settings
from app.models.token_black_list import TokenBlackList
from app.models.user import User
from app.schemas.auth import RefreshTokenSchema


def create_tokens(user_id: int) -> tuple[str, str]:
    return (
        security.create_jwt_token(user_id=user_id, token_type="access"),
        security.create_jwt_token(user_id=user_id, token_type="refresh")
    )


def blacklist_refresh_token(db: Session, token: str, expires_at_timestamp: int) -> bool:
    """
    Blocks a refresh token if blacklisting is enabled in settings.
    Converts the JWT 'exp' timestamp into a proper datetime object.
    """
    if not settings.REFRESH_TOKEN_BLACKLIST:
        return False

    expires_at_dt = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)

    blacklisted_token = TokenBlackList(
        refresh_token=token,
        expires_at=expires_at_dt
    )

    db.add(blacklisted_token)
    db.commit()
    return True


def is_blacklisted(db: Session, token: str) -> bool:
    """
    Checks if a token exists in our database blacklist.
    """
    if not settings.REFRESH_TOKEN_BLACKLIST:
        return False

    return db.query(TokenBlackList).filter(TokenBlackList.refresh_token == token).first() is not None


def refresh_access_token(db: Session, payload: RefreshTokenSchema) -> tuple[str, str]:
    # 1. REUSE DETECTION GAPS HOOK:
    # If someone tries to use a refresh token that is ALREADY in the blacklist database table,
    # it means a breach or replay attack is happening!
    if is_blacklisted(db, payload.refresh_token):
        # Decode the compromised token to find out who it belonged to
        try:
            token_data = security.decode_jwt_token(payload.refresh_token)
            user_id = token_data.get("sub")

            if user_id:
                # PUNISHMENT: Instantly set logged_out_at to NOW.
                # This instantly kills EVERY active access token across all devices for this user.
                db.query(User).filter(User.id == int(user_id)).update(
                    {User.logged_out_at: datetime.now(timezone.utc)}
                )
                db.commit()
        except Exception:
            pass  # Fallback if token decoding fails entirely

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security Alert: This token has already been used. All sessions revoked."
        )

    # 2. Decode token normally
    token_data = security.decode_jwt_token(payload.refresh_token)

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. A refresh token is required."
        )

    user_id = token_data.get("sub")
    exp_timestamp = token_data.get("exp")
    issued_at_timestamp = token_data.get("iat")

    if exp_timestamp is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token. Missing expiration claim."
        )

    # 3. Standard global logout grace period check
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user and user.logged_out_at and issued_at_timestamp:
        token_issued_at = datetime.fromtimestamp(issued_at_timestamp, tz=timezone.utc)
        if token_issued_at < user.logged_out_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please log in again."
            )

    # 4. ROTATION GUARD: Securely burn the old refresh token so it triggers step 1 if seen again
    blacklist_refresh_token(
        db=db,
        token=payload.refresh_token,
        expires_at_timestamp=exp_timestamp
    )

    return create_tokens(int(user_id))
