# notes-fastapi/app/schemas/user.py
from datetime import datetime, date

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.schemas.validators import validate_username_string, validate_password_complexity


class UserCreateSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_validator(cls, v: str) -> str:
        return validate_username_string(v)

    @field_validator("password")
    @classmethod
    def password_validator(cls, v: str) -> str:
        return validate_password_complexity(v)


class UserUpdateSchema(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

    @field_validator("username")
    @classmethod
    def username_validator(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_username_string(v)
        return v


class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    is_active: bool
    is_superuser: bool
    is_staff: bool
    logged_out_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
