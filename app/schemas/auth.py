# notes-fastapi/app/schemas/auth.py
from pydantic import BaseModel

from app.schemas.user import UserResponseSchema


class LoginSchema(BaseModel):
    identifier: str
    password: str


class LoginResponseSchema(BaseModel):
    user: UserResponseSchema
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class RefreshTokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
