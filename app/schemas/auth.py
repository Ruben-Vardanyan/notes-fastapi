# notes-fastapi/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, field_validator

from app.schemas.user import UserResponseSchema
from app.schemas.validators import validate_password_complexity


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


class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_validator(cls, v: str) -> str:
        return validate_password_complexity(v)
