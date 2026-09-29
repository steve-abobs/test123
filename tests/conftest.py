from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.dependencies import get_search_backend
from app.main import app
from tests.fakes import InMemorySearchBackend


@pytest_asyncio.fixture
async def client_with_backend() -> AsyncIterator[tuple[AsyncClient, async_sessionmaker, InMemorySearchBackend]]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)
    backend = InMemorySearchBackend()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    def override_get_search_backend() -> InMemorySearchBackend:
        return backend

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_search_backend] = override_get_search_backend

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_maker, backend

    app.dependency_overrides.clear()
    await test_engine.dispose()
