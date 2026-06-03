# notes-fastapi/app/models/base.py

from app.core.database import Base  # noqa
from app.models.user import User  # noqa
from app.models.token_black_list import TokenBlackList  # noqa
from app.models.verification_code import VerificationCode  # noqa
from app.models.note import Note # noqa
from app.models.note_collaborator import NoteCollaborator # noqa
