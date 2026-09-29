async def test_health_check(client_with_backend):
    client, _, _ = client_with_backend
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
