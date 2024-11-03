from typing import Annotated
from fastapi import Depends
from pydantic import TypeAdapter

from common.model import CollectorInfo


state_type_adapter = TypeAdapter(set[CollectorInfo])
state = state_type_adapter.validate_python([])


async def get_state() -> set[CollectorInfo]:
    return state


StateDep = Annotated[set[CollectorInfo], Depends(get_state)]
