import os
from fastapi import status
from httpx import ASGITransport, AsyncClient
import pytest
from common.model import (
    Container,
    UnsupportedWasteType,
    WasteTypeMapping,
)
from tests.suites import *


@pytest.fixture
async def client(registry: RegistryContainer):
    os.environ["COLLECTOR_DB_URI"] = f"sqlite:///:memory:"
    os.environ["COLLECTOR_SELF_URL"] = "0.0.0.0:0000"
    os.environ["COLLECTOR_REGISTRY_URL"] = registry.url
    os.environ["COLLECTOR_POSITION_X"] = "5"
    os.environ["COLLECTOR_POSITION_Y"] = "10"

    from collector.main import app, lifespan
    async with lifespan(app):
        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://localhost"
        ) as client:
            yield client


async def test_health(client: AsyncClient, anyio_backend: Any):
    response = await client.get("/health")
    assert response.status_code == 204


async def test_self_on_registry(client: AsyncClient, registry: RegistryContainer, anyio_backend: Any):
    async with AsyncClient(base_url=registry.url) as client:
        response = await client.get("/registry/collectors")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"position": {"x": 5, "y": 10}, "url": "0.0.0.0:0000"}]


async def test_state_lifecycle(client: AsyncClient, anyio_backend: Any):
    # Step 1. Test that initially collector has no containers
    response = await client.get("/collector")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {}

    # Step 2. Test that validation of the new requested state will fail
    invalid_state = {"glass": {"max": 50}, "bio": {"current": 20, "max": 10}}
    response = await client.put("/collector", json=invalid_state)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Step 3. Test that new requested state will be accepted and collector's state has changed
    state = {"glass": {"max": 50}, "bio": {"current": 20, "max": 30}}
    response = await client.put("/collector", json=state)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await client.get("/collector")
    assert response.status_code == status.HTTP_200_OK
    assert WasteTypeMapping[Container].model_validate(
        response.json()
    ) == WasteTypeMapping[Container].model_validate(state)

    # Step 4. Test that sended wastes didn't fit
    wastes = {"bio": 20, "plastic": 5}
    response = await client.patch("/collector", json=wastes)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"bio": 10, "plastic": UnsupportedWasteType}

    # Step 5. Test that sended wastes recieved by collector
    wastes = {"bio": 5, "glass": 50}
    response = await client.patch("/collector", json=wastes)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Step 6. Test that containers have cleared
    response = await client.delete("/collector")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await client.get("/collector")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "glass": {"current": 0, "max": 50},
        "bio": {"current": 0, "max": 30},
    }
