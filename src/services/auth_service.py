from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.repositories.token_repo import TokenRepository
from src.repositories.user_repo import UserRepository
from src.schemas.auth import AccessTokenResponse, TokenResponse, UserCreate, UserOut


class AuthService:
    def __init__(self, user_repo: UserRepository, token_repo: TokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def register(self, data: UserCreate) -> UserOut:
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        if await self.user_repo.get_by_username(data.username):
            raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
        user = await self.user_repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        return UserOut.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive user")

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        await self.token_repo.create(refresh_token, user.id, expires_at)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")

        rt = await self.token_repo.get_valid(refresh_token)
        if not rt:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

        await self.token_repo.revoke(rt)
        new_access = create_access_token(payload["sub"])
        return AccessTokenResponse(access_token=new_access)
