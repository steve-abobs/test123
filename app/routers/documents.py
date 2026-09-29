from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_session
from app.dependencies import get_search_backend
from app.schemas import DeleteResponse
from app.services import delete_document

router = APIRouter(tags=["documents"])


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Удалить документ",
    description="Удаляет документ из БД и из поискового индекса по полю id.",
)
async def remove_document(
    document_id: int,
    session=Depends(get_session),
    backend=Depends(get_search_backend),
) -> DeleteResponse:
    deleted = await delete_document(session, backend, document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DeleteResponse(id=document_id, deleted=True)
