from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk


class SearchBackend(ABC):
    """Abstraction over the full-text search index used by the service.

    Keeping this as an interface lets the API layer stay agnostic of the
    concrete search engine and makes it possible to swap in a test double
    without touching routes or business logic.
    """

    @abstractmethod
    async def ensure_index(self) -> None: ...

    @abstractmethod
    async def index_document(self, doc_id: int, text: str) -> None: ...

    @abstractmethod
    async def index_documents(self, documents: Iterable[dict]) -> None: ...

    @abstractmethod
    async def delete_document(self, doc_id: int) -> bool: ...

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[int]: ...

    @abstractmethod
    async def close(self) -> None: ...


class ElasticsearchBackend(SearchBackend):
    def __init__(self, url: str, index_name: str) -> None:
        self._client = AsyncElasticsearch(hosts=[url])
        self._index_name = index_name

    async def ensure_index(self) -> None:
        if not await self._client.indices.exists(index=self._index_name):
            await self._client.indices.create(
                index=self._index_name,
                mappings={
                    "properties": {
                        "id": {"type": "long"},
                        "text": {"type": "text"},
                    }
                },
            )

    async def index_document(self, doc_id: int, text: str) -> None:
        await self._client.index(
            index=self._index_name,
            id=str(doc_id),
            document={"id": doc_id, "text": text},
        )

    async def index_documents(self, documents: Iterable[dict]) -> None:
        actions = (
            {"_index": self._index_name, "_id": str(doc["id"]), "_source": doc}
            for doc in documents
        )
        await async_bulk(self._client, actions)

    async def delete_document(self, doc_id: int) -> bool:
        try:
            await self._client.delete(index=self._index_name, id=str(doc_id))
            return True
        except NotFoundError:
            return False

    async def search(self, query: str, limit: int) -> list[int]:
        response = await self._client.search(
            index=self._index_name,
            query={"match": {"text": query}},
            size=limit,
            source=False,
        )
        return [int(hit["_id"]) for hit in response["hits"]["hits"]]

    async def close(self) -> None:
        await self._client.close()
