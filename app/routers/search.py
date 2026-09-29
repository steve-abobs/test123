from fastapi import APIRouter, Depends, Query

from app.database import get_session
from app.dependencies import get_search_backend
from app.schemas import DocumentOut, SearchResponse
from app.services import search_documents

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Поиск документов по тексту",
    description=(
        "Ищет документы по тексту в поисковом индексе и возвращает первые 20 "
        "документов со всеми полями БД, упорядоченные по дате создания (по убыванию)."
    ),
)
async def search(
    q: str = Query(..., min_length=1, description="Текстовый запрос для поиска по тексту документа"),
    session=Depends(get_session),
    backend=Depends(get_search_backend),
) -> SearchResponse:
    documents = await search_documents(session, backend, q)
    return SearchResponse(
        query=q,
        count=len(documents),
        results=[DocumentOut.model_validate(document) for document in documents],
    )
