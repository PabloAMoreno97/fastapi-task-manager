import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.routers import auth, health, tasks
from src.core.config import settings
from src.core.rate_limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "msg": "%(message)s"}',
)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Production-ready task management REST API. "
        "Authenticate via /auth/register + /auth/login to get JWT tokens, "
        "then use them in the Authorization header for all /tasks endpoints."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(health.router)
