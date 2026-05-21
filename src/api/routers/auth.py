from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_session
from src.core.rate_limiter import limiter
from src.repositories.token_repo import TokenRepository
from src.repositories.user_repo import UserRepository
from src.schemas.auth import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserOut
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(UserRepository(session), TokenRepository(session))


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Register a new user",
    responses={409: {"description": "Email or username already taken"}},
)
async def register(data: UserCreate, service: AuthService = Depends(_service)):
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and get JWT tokens",
    responses={401: {"description": "Invalid credentials"}},
)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, service: AuthService = Depends(_service)):
    return await service.login(data.email, data.password)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Exchange a refresh token for a new access token",
    responses={401: {"description": "Invalid or expired refresh token"}},
)
async def refresh(data: RefreshRequest, service: AuthService = Depends(_service)):
    return await service.refresh(data.refresh_token)
