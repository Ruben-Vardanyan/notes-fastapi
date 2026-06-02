# notes-fastapi/app/services/auth_services/reset_password_service.py
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationType


def execute_password_reset(db: Session, token: str, new_password: str):
    """Validates the reset token state, applies the new hashed credential, and invalidates sessions."""
    # 1. Lookup the token under the correct purpose parameters
    verification_record = db.query(VerificationCode).filter(
        VerificationCode.token == token,
        VerificationCode.purpose == VerificationType.PASSWORD_RESET
    ).first()

    # 2. Strict State Verifications
    if not verification_record:
        raise HTTPException(status_code=404, detail="Invalid or expired reset token.")

    if verification_record.used_at is not None:
        raise HTTPException(status_code=400, detail="This reset token has already been used.")

    # 3. Micro-Lifespan Validation (15 minutes check)
    current_now = datetime.now(timezone.utc)
    record_expiry = verification_record.expires_at.replace(tzinfo=timezone.utc)

    if current_now > record_expiry:
        raise HTTPException(status_code=400, detail="This password reset link has expired.")

    # 4. Fetch the target account
    user = db.query(User).filter(User.id == verification_record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Associated user account not found.")

    # 5. Apply Credentials & Burn Token
    user.hashed_password = hash_password(new_password)
    verification_record.used_at = current_now

    # 6. GLOBAL LOGOUT SECURITY TRIGGER:
    # Updates the user's logged_out_at timestamp to instantly invalidate every active
    # access token currently circulating on the user's other devices.
    user.logged_out_at = current_now

    db.commit()
