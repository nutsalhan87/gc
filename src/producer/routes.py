from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, Path, status
from pydantic import PositiveInt

from common.model import HTTPExceptionModel, WasteType, WasteTypeMapping
from producer.schema import Order
from producer.service import OrderServiceDep


router = APIRouter(prefix="/producer")


@router.post(
    path="/wastes",
    summary="Create order to send wastes to a collector",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Order,
    response_model_exclude_none=True,
)
async def send_wastes(
    wastes: Annotated[
        WasteTypeMapping[PositiveInt], # TODO: validate that any not none
        Body(
            examples=[
                {
                    WasteType.bio: 90,
                    WasteType.plastic: 5,
                }
            ],
        ),
    ],
    order_service: OrderServiceDep
):
    return await order_service.send_wastes(wastes)


@router.get(
    path="/order/{id}",
    summary="Get the order information",
    status_code=status.HTTP_200_OK,
    response_model=Order,
    response_model_exclude_none=True,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "No order with this ID was found",
            "model": HTTPExceptionModel,
        }
    }
)
async def order_info(id: Annotated[int, Path()], order_service: OrderServiceDep):
    result = await order_service.get_order_info(id)
    if result is not None:
        return result
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
