import asyncio
import os
from fastapi import status
from httpx import ASGITransport, AsyncClient
import pytest
from producer.schema import OrderStatus
from tests.suites import *


@pytest.fixture(scope="module")
async def client(collector: CollectorContainer, anyio_backend: Any):
    async with AsyncClient(base_url=collector.url) as client:
        await client.put("/collector", json={"glass": {"current": 10, "max": 20}})

    os.environ["PRODUCER_REGISTRY_URL"] = collector.registry.url
    os.environ["PRODUCER_POSITION_X"] = "0"
    os.environ["PRODUCER_POSITION_Y"] = "0"
    from producer.main import app, lifespan

    async with lifespan(app):
        async with AsyncClient(
            transport=ASGITransport(app), base_url="http://localhost"
        ) as client:
            yield client


async def test_health(client: AsyncClient, anyio_backend: Any):
    response = await client.get("/health")
    assert response.status_code == 204


async def test_success_order(client: AsyncClient, anyio_backend: Any):
    wastes = {"glass": 5}
    response = await client.post("/producer/wastes", json=wastes)
    created_order = response.json()
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert created_order["wastes"] == wastes
    assert created_order["status"] == OrderStatus.ACCEPTED

    await asyncio.sleep(0.5)

    response = await client.get(f"/producer/order/{created_order['id']}")
    order = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert order["wastes"] == wastes
    assert order["status"] == OrderStatus.SUCCESS


async def test_rejected_order(client: AsyncClient, anyio_backend: Any):
    # Step 1. Test that collectors don't have such waste type container
    wastes = {"bio": 10}
    response = await client.post("/producer/wastes", json=wastes)
    created_order = response.json()
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert created_order["wastes"] == wastes
    assert created_order["status"] == OrderStatus.ACCEPTED

    await asyncio.sleep(0.5)

    response = await client.get(f"/producer/order/{created_order['id']}")
    order = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert order["wastes"] == wastes
    assert order["status"] == OrderStatus.REJECTED

    # Step 2. Test that sended wastes didn't fit in any collector
    wastes = {"glass": 15}
    response = await client.post("/producer/wastes", json=wastes)
    created_order = response.json()
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert created_order["wastes"] == wastes
    assert created_order["status"] == OrderStatus.ACCEPTED

    await asyncio.sleep(0.5)

    response = await client.get(f"/producer/order/{created_order['id']}")
    order = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert order["wastes"] == wastes
    assert order["status"] == OrderStatus.REJECTED


async def test_order_not_found(client: AsyncClient, anyio_backend: Any):
    response = await client.get("/order/99999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
