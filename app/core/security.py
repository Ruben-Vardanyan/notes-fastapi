from datetime import timedelta

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext
from starlette import status

from app.core import timezone
from app.core.config import settings

# --- password ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password):
    # Generated a encrypted password
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    # Compares a login attempt password against the database stored hash.
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Token Utilities ---

def create_jwt_token(user_id: int, token_type: str = "access"):
    # Generates a signed JWT token.
    # user_id => user ID
    # token_type => "access" or "refresh"
    now = timezone.now()

    if token_type == "access":
        expire = now + settings.ACCESS_TOKEN_LIFETIME
    elif token_type == "refresh":
        expire = now + settings.REFRESH_TOKEN_LIFETIME
    else:
        raise ValueError("Invalid token type. Use 'access' or 'refresh'")

    payload = {
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "sub": str(user_id),
        "type": token_type
    }

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_jwt_token(token: str) -> dict:
    """
    Decodes an incoming JWT token string.
    Intercepts signature errors to keep services clean.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
