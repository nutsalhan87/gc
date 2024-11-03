from fastapi import status
from httpx import ASGITransport, AsyncClient
import pytest
from common.model import CollectorInfo, Position
from registry.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        yield client


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_collector_lifecycle(client: AsyncClient):
    # Step 1. Test that there is no collectors in the registry
    response = await client.get("/registry/collectors")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    collector = CollectorInfo(position=Position(x=1, y=1), url="0.0.0.0:0000")

    # Step 2. Test that collector registered
    response = await client.put("/registry/collector", json=collector.model_dump())
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Step 3. Test that collector can't be registered twice
    response = await client.put("/registry/collector", json=collector.model_dump())
    assert response.status_code == status.HTTP_409_CONFLICT

    # Step 4. Test that registered collector can be received
    response = await client.get("/registry/collectors")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [collector.model_dump()]

    # Step 5. Test that collector deregistered
    response = await client.request(
        "DELETE", "/registry/collector", json=collector.model_dump()
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Step 5. Test that there is no collectors in the registry
    response = await client.get("/registry/collectors")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
