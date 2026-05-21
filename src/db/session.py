from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings

engine = create_async_engine(settings.database_url, connect_args=settings.ssl_connect_args, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
