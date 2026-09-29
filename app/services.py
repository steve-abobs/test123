from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Document
from app.search_backend import SearchBackend


async def search_documents(
    session: AsyncSession,
    backend: SearchBackend,
    query: str,
    limit: int = settings.search_result_limit,
) -> list[Document]:
    """Full-text search in the index, final ordering/limit applied in the DB.

    The index only stores id/text, so relevance matching happens there while
    the created_date ordering the API contract requires is resolved against
    the database, which is the source of truth for that field.
    """
    matched_ids = await backend.search(query, limit=settings.search_candidate_pool_size)
    if not matched_ids:
        return []

    stmt = (
        select(Document)
        .where(Document.id.in_(matched_ids))
        .order_by(Document.created_date.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_document(session: AsyncSession, backend: SearchBackend, document_id: int) -> bool:
    document = await session.get(Document, document_id)
    db_deleted = document is not None
    if document is not None:
        await session.delete(document)
        await session.commit()

    es_deleted = await backend.delete_document(document_id)
    return db_deleted or es_deleted
