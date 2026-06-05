# notes-fastapi/app/schemas/validators.py
import re


def validate_username_string(username: str) -> str:
    username = username.strip()

    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long")
    if len(username) > 50:
        raise ValueError("Username cannot exceed 50 characters")
    if not re.match(r"^\w+$", username):
        raise ValueError("Username can only contain letters, numbers, and underscores")

    return username


def validate_password_complexity(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter")

    return password
