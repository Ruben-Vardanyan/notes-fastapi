# notes-fastapi/app/core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

# get_remote_address tracks requests based on the client's IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
