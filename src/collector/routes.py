from typing import Annotated, Literal
from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from pydantic import Field, PositiveInt

from collector.service import ContainersServiceDep
from common.model import Container, UnsupportedWasteType, UnsupportedWasteTypeLiteral, WasteType, WasteTypeMapping


router = APIRouter(prefix="/collector")


@router.put(
    path="",
    summary="Set collector's state",
    tags=["management"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def set_state(
    containers: WasteTypeMapping[Container], containers_service: ContainersServiceDep
):
    await containers_service.set(containers)


@router.delete(
    path="",
    summary="Clear the collector",
    tags=["management"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear(containers_service: ContainersServiceDep):
    await containers_service.clear()


@router.get(
    path="",
    summary="Get info about containers",
    tags=["client"],
    response_model=WasteTypeMapping[Container],
    response_model_exclude_none=True,
)
async def info(containers_service: ContainersServiceDep):
    return await containers_service.info()


@router.patch(
    path="",
    summary="Recieve the wastes",
    description="Waste will be received only if there is enough space for all of it",
    tags=["client"],
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_model_exclude_none=True,
    response_description="Collector successfully received the waste",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "There is no space for some of the waste types.\n\n"
            "Number value in schema means amount of waste that didn't fit into the container.",
            "model": Annotated[
                WasteTypeMapping[PositiveInt | UnsupportedWasteTypeLiteral],
                Field(
                    examples=[
                        {
                            WasteType.bio: 20,
                            WasteType.glass: UnsupportedWasteType,
                        }
                    ]
                ),
            ],
        }
    },
)
async def receive_waste(
    wastes: Annotated[
        WasteTypeMapping[PositiveInt],
        Body(
            examples=[
                {
                    WasteType.bio: 90,
                    WasteType.plastic: 5,
                }
            ]
        ),
    ],
    containersService: ContainersServiceDep,
):
    result: (
        WasteTypeMapping[PositiveInt | UnsupportedWasteTypeLiteral] | Literal[True]
    ) = await containersService.put(wastes)
    if result == True:
        return
    else:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=result.model_dump(exclude_none=True),
        )
