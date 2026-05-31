# notes-fastapi/app/core/timezone.py
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.config import settings


def now() -> datetime:
    """
    Returns the current datetime in the configured application timezone.
    Replicates Django's timezone.now() behavior.
    """
    return datetime.now(ZoneInfo(settings.TIMEZONE))
