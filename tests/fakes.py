"""In-memory SearchBackend test double.

Lets functional tests exercise the real API/service/DB layers over HTTP
without requiring a running Elasticsearch instance.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.search_backend import SearchBackend


class InMemorySearchBackend(SearchBackend):
    def __init__(self) -> None:
        self._store: dict[int, str] = {}

    async def ensure_index(self) -> None:
        return None

    async def index_document(self, doc_id: int, text: str) -> None:
        self._store[doc_id] = text

    async def index_documents(self, documents: Iterable[dict]) -> None:
        for document in documents:
            self._store[document["id"]] = document["text"]

    async def delete_document(self, doc_id: int) -> bool:
        return self._store.pop(doc_id, None) is not None

    async def search(self, query: str, limit: int) -> list[int]:
        needle = query.lower()
        matches = [doc_id for doc_id, text in self._store.items() if needle in text.lower()]
        return matches[:limit]

    async def close(self) -> None:
        return None
