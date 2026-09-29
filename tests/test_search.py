from datetime import datetime, timedelta

from tests.utils import seed_document


async def test_search_returns_matches_ordered_by_created_date(client_with_backend):
    client, session_maker, backend = client_with_backend

    await seed_document(
        session_maker, backend,
        text="python asyncio tutorial",
        created_date=datetime(2020, 1, 1),
        rubrics=["tech"],
    )
    newer_id = await seed_document(
        session_maker, backend,
        text="asyncio in python explained",
        created_date=datetime(2021, 5, 5),
        rubrics=["tech"],
    )
    await seed_document(
        session_maker, backend,
        text="unrelated cooking recipe",
        created_date=datetime(2022, 1, 1),
        rubrics=["food"],
    )

    response = await client.get("/search", params={"q": "asyncio"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    result_ids = [doc["id"] for doc in payload["results"]]
    assert result_ids[0] == newer_id
    for doc in payload["results"]:
        assert {"id", "rubrics", "text", "created_date"} <= doc.keys()


async def test_search_limits_results_to_20(client_with_backend):
    client, session_maker, backend = client_with_backend

    base_date = datetime(2020, 1, 1)
    for i in range(25):
        await seed_document(
            session_maker, backend,
            text=f"needle occurrence {i}",
            created_date=base_date + timedelta(days=i),
        )

    response = await client.get("/search", params={"q": "needle"})
    payload = response.json()

    assert payload["count"] == 20
    dates = [doc["created_date"] for doc in payload["results"]]
    assert dates == sorted(dates, reverse=True)


async def test_search_without_matches_returns_empty_list(client_with_backend):
    client, session_maker, backend = client_with_backend
    await seed_document(session_maker, backend, text="hello world", created_date=datetime(2020, 1, 1))

    response = await client.get("/search", params={"q": "nonexistent"})

    assert response.status_code == 200
    assert response.json()["results"] == []


async def test_search_requires_query_param(client_with_backend):
    client, _, _ = client_with_backend
    response = await client.get("/search")
    assert response.status_code == 422
