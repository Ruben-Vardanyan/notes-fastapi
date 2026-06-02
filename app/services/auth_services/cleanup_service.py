# notes-fastapi\app\services\auth_services\cleanup_service.py
from datetime import datetime, timezone, timedelta

from app.core.database import SessionLocal
from app.models.token_black_list import TokenBlackList
from app.models.verification_code import VerificationCode


def clean_expired_verification_codes():
    """
    Scheduler
    """
    db = SessionLocal()

    try:
        current_now = datetime.now(timezone.utc)

        deleted_count = db.query(VerificationCode).filter(
            (VerificationCode.expires_at < current_now) |
            (VerificationCode.used_at != None)
        ).delete(synchronize_session=False)

        db.commit()

        if deleted_count > 0:
            print(f"[Janitor - Verification] Cleaned up {deleted_count} expired verification codes.")

    except Exception as e:
        db.rollback()
        print(f"[Janitor - Verification] Failed: {e}")
    finally:
        db.close()


def clean_blacklisted_tokens():
    """
    Scheduler
    """
    db = SessionLocal()

    try:
        current_now = datetime.now(timezone.utc) - timedelta(days=7)

        deleted_count = db.query(TokenBlackList).filter(
            (TokenBlackList.expires_at < current_now)
        ).delete(synchronize_session=False)

        db.commit()

        if deleted_count > 0:
            print(f"[Janitor - TokenBlackList] Cleaned up {deleted_count} expired tokens.")

    except Exception as e:
        db.rollback()
        print(f"[Janitor - TokenBlackList] Failed: {e}")
    finally:
        db.close()
