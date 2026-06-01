# notes-fastapi/main.py
from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.urls import v1_router
from app.core.config import settings
from app.core.limiter import limiter

app = FastAPI(title=settings.PROJECT_NAME)


# 1. Custom Middleware to bypass docs (Declared FIRST so it wraps the app correctly)
@app.middleware("http")
async def skip_limiter_for_docs(request: Request, call_next):
    # Explicitly bypass documentation and root endpoints
    # This prevents accidental string matching bugs on your sub-routes
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"] or request.url.path.startswith("/docs"):
        request.state.limiter_bypass = True
    return await call_next(request)


# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the limiter to the app state
app.state.limiter = limiter
# Register the default 429 error handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(v1_router, prefix=settings.API_V1_STR)


@app.get("/")
def home_check():
    return {"status": "API is running smoothly"}
