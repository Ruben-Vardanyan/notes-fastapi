# notes-fastapi/app/api/v1/urls.py
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router

# The main router for all V1 endpoints
v1_router = APIRouter()

# urls
v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
