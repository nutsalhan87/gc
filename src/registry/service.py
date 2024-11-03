from typing import Annotated
from aiorwlock import RWLock
from fastapi import Depends
from common.model import CollectorInfo
from registry.state import StateDep

_lock = RWLock()

class CollectorService:
    def __init__(self, state: StateDep) -> None:
        self.state = state

    async def get_collectors(self) -> set[CollectorInfo]:
        async with _lock.reader_lock:
            return self.state.copy()

    async def put_collector(self, collector: CollectorInfo) -> bool:
        async with _lock.writer_lock:
            if collector in self.state:
                return False
            else:
                self.state.add(collector)
                return True

    async def remove_collector(self, collector: CollectorInfo):
        async with _lock.writer_lock:
            self.state.discard(collector)


CollectorServiceDep = Annotated[CollectorService, Depends()]
