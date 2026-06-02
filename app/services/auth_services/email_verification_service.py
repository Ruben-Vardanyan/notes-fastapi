# notes-fastapi/app/services/auth_services/email_verification_service.py
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationType
from app.services.auth_services.email_service import send_activation_email


def create_and_send_verification(
        db: Session,
        current_user: User,
        background_tasks: BackgroundTasks
):
    """Renamed to avoid endpoint namespace confusion."""
    if current_user.is_active:
        raise HTTPException(status_code=400, detail="User is already verified and active.")

    current_now = datetime.now(timezone.utc)
    db.query(VerificationCode).filter(
        VerificationCode.user_id == current_user.id,
        VerificationCode.purpose == VerificationType.EMAIL_VERIFICATION,
        VerificationCode.used_at == None,
        VerificationCode.expires_at > current_now,
    ).update({VerificationCode.expires_at: current_now})

    secure_token = secrets.token_urlsafe(32)
    expiration_time = current_now + timedelta(hours=24)

    db_code = VerificationCode(
        user_id=current_user.id,
        token=secure_token,
        purpose=VerificationType.EMAIL_VERIFICATION,
        expires_at=expiration_time
    )

    db.add(db_code)
    db.commit()

    background_tasks.add_task(
        send_activation_email,
        email_to=current_user.email,
        username=current_user.username,
        token=secure_token
    )


def execute_email_verification(db: Session, token: str):
    """Processes verification token lifecycle database executions."""
    verification_record = db.query(VerificationCode).filter(
        VerificationCode.token == token,
        VerificationCode.purpose == VerificationType.EMAIL_VERIFICATION
    ).first()

    if not verification_record:
        raise HTTPException(status_code=404, detail="Invalid verification link.")

    if verification_record.used_at is not None:
        raise HTTPException(status_code=400, detail="This token has already been consumed.")

    current_now = datetime.now(timezone.utc)
    record_expiry = verification_record.expires_at.replace(tzinfo=timezone.utc)

    if current_now > record_expiry:
        raise HTTPException(status_code=400, detail="This activation link has expired.")

    user_to_activate = db.query(User).filter(User.id == verification_record.user_id).first()
    if not user_to_activate:
        raise HTTPException(status_code=404, detail="Associated user account not found.")

    user_to_activate.is_active = True
    verification_record.used_at = current_now

    db.commit()
