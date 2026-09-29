from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rubrics: list[str]
    text: str
    created_date: datetime


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[DocumentOut]


class DeleteResponse(BaseModel):
    id: int
    deleted: bool
