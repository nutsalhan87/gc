from asyncio import Lock, Queue
from typing import Annotated, NoReturn
from aiorwlock import RWLock
from fastapi import Depends, logger, status
from httpx import AsyncClient
from pydantic import PositiveInt, TypeAdapter

from common.model import CollectorInfo, WasteTypeMapping
from producer.settings import settings
from producer.schema import Order, OrderStatus
from producer.util import distance_to_collector

_cnt = 0
_cnt_lock = Lock()

_all_orders: dict[int, Order] = dict()
_orders_lock = RWLock()

_unprosecced_orders: Queue[Order] = Queue()


async def process_orders_routine() -> NoReturn:
    client = AsyncClient(base_url=settings.registry_url)
    while True:
        order = await _unprosecced_orders.get()
        result = await client.get("/registry/collectors")
        collectors = TypeAdapter(list[CollectorInfo]).validate_json(result.text)
        for collector in sorted(collectors, key=distance_to_collector):
            async with AsyncClient(base_url=collector.url) as collector_client:
                result = await collector_client.patch("/collector", json=order.wastes.model_dump())
            if result.status_code == status.HTTP_204_NO_CONTENT:
                order.status = OrderStatus.SUCCESS
                break
            elif result.status_code != status.HTTP_409_CONFLICT:
                logger.logger.error(result.content)
        if order.status == OrderStatus.ACCEPTED:
            order.status = OrderStatus.REJECTED


class OrderService:
    async def send_wastes(self, wastes: WasteTypeMapping[PositiveInt]) -> Order:
        async with _cnt_lock:
            global _cnt
            id = _cnt
            _cnt += 1
        order = Order(id=id, wastes=wastes, status=OrderStatus.ACCEPTED)
        async with _orders_lock.writer_lock:
            _all_orders[id] = order
        await _unprosecced_orders.put(order)
        return order

    async def get_order_info(self, id: int) -> Order | None:
        async with _orders_lock.reader_lock:
            return _all_orders.get(id)


OrderServiceDep = Annotated[OrderService, Depends()]
