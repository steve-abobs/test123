from datetime import datetime

from tests.utils import seed_document


async def test_delete_removes_document_from_db_and_index(client_with_backend):
    client, session_maker, backend = client_with_backend
    doc_id = await seed_document(
        session_maker, backend, text="document to be deleted", created_date=datetime(2020, 1, 1)
    )

    response = await client.delete(f"/documents/{doc_id}")

    assert response.status_code == 200
    assert response.json() == {"id": doc_id, "deleted": True}
    assert await backend.search("deleted", limit=10) == []

    search_response = await client.get("/search", params={"q": "deleted"})
    assert search_response.json()["results"] == []


async def test_delete_nonexistent_document_returns_404(client_with_backend):
    client, _, _ = client_with_backend
    response = await client.delete("/documents/999999")
    assert response.status_code == 404


async def test_delete_removes_from_index_even_if_only_dangling_there(client_with_backend):
    client, _, backend = client_with_backend
    await backend.index_document(42, "orphan index entry")

    response = await client.delete("/documents/42")

    assert response.status_code == 200
    assert await backend.search("orphan", limit=10) == []
