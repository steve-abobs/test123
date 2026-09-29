from datetime import datetime

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Document
from tests.fakes import InMemorySearchBackend


async def seed_document(
    session_maker: async_sessionmaker,
    backend: InMemorySearchBackend,
    *,
    text: str,
    created_date: datetime,
    rubrics: list[str] | None = None,
) -> int:
    async with session_maker() as session:
        document = Document(text=text, created_date=created_date, rubrics=rubrics or [])
        session.add(document)
        await session.flush()
        await backend.index_document(document.id, document.text)
        await session.commit()
        return document.id
