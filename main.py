# notes-fastapi/main.py
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.urls import v1_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix=settings.API_V1_STR)

@app.get("/")
def home_check():
    return {"status": "API is running smoothly"}
