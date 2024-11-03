from typing import Annotated
from fastapi import APIRouter, Body, HTTPException, status

from common.model import CollectorInfo, HTTPExceptionModel
from registry.service import CollectorServiceDep


router = APIRouter(prefix="/registry")


@router.get(
    "/collectors",
    summary="Get collectors' information",
    response_model=set[CollectorInfo],
)
async def get(collectorService: CollectorServiceDep):
    return await collectorService.get_collectors()


@router.put(
    "/collector",
    summary="Register collector",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Collector already registered",
            "model": HTTPExceptionModel,
        }
    },
)
async def register(
    collector: Annotated[CollectorInfo, Body()], collectorService: CollectorServiceDep
):
    if await collectorService.put_collector(collector):
        return
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This collector already exist"
        )


@router.delete(
    "/collector", summary="Deregister collector", status_code=status.HTTP_204_NO_CONTENT
)
async def remove(
    collector: Annotated[CollectorInfo, Body()], collectorService: CollectorServiceDep
):
    await collectorService.remove_collector(collector)
    return
