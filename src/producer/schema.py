from enum import Enum

from pydantic import BaseModel, PositiveInt

from common.model import WasteTypeMapping


class OrderStatus(str, Enum):
    ACCEPTED = "Accepted"
    SUCCESS = "Success"
    REJECTED = "Rejected"


class Order(BaseModel):
    id: int
    wastes: WasteTypeMapping[PositiveInt]
    status: OrderStatus
