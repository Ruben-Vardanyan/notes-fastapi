# notes-fastapi/app/services/auth_services/forgot_password_service.py
import secrets
from datetime import datetime, timezone, timedelta

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.verification_code import VerificationCode, VerificationType
from app.services.auth_services.email_service import send_password_reset_email


def process_forgot_password(
        db: Session,
        email: str,
        background_tasks: BackgroundTasks
):
    """Validates the email source, invalidates older tokens, and setups a reset window."""
    # 1. Look up the user by email
    user = db.query(User).filter(User.email == email).first()

    # 2. SECURITY: User Enumeration Protection
    # If the email isn't registered, we return silently without throwing an error.
    # This keeps malicious actors blind to who has an account on your app.
    if not user or not user.is_active:
        return

    current_now = datetime.now(timezone.utc)

    # 3. Ghost Token Prevention
    # Clean up any previously issued, active password reset tokens for this user
    db.query(VerificationCode).filter(
        VerificationCode.user_id == user.id,
        VerificationCode.purpose == VerificationType.PASSWORD_RESET,
        VerificationCode.used_at == None,
        VerificationCode.expires_at > current_now
    ).update({VerificationCode.expires_at: current_now})

    # 4. Generate high-entropy reset token
    secure_token = secrets.token_urlsafe(32)

    # Tight Security: Password tokens are highly volatile and last only 15 minutes
    expiration_time = current_now + timedelta(minutes=15)

    # 5. Commit token properties to the database
    db_code = VerificationCode(
        user_id=user.id,
        token=secure_token,
        purpose=VerificationType.PASSWORD_RESET,
        expires_at=expiration_time
    )
    db.add(db_code)
    db.commit()

    # 6. Offload SMTP transport to a background worker threads
    background_tasks.add_task(
        send_password_reset_email,
        email_to=user.email,
        username=user.username,
        token=secure_token
    )
