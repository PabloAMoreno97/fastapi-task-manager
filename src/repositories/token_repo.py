import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.token import RefreshToken


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: str, user_id: uuid.UUID, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
        self.session.add(rt)
        await self.session.commit()
        return rt

    async def get_valid(self, token: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        rt = result.scalar_one_or_none()
        if rt is None:
            return None
        # Check expiry in Python to avoid SQLite timezone comparison quirks
        expires = rt.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return rt if expires > datetime.now(timezone.utc) else None

    async def revoke(self, rt: RefreshToken) -> None:
        rt.is_revoked = True
        await self.session.commit()
