from contextlib import asynccontextmanager
from fastapi import FastAPI, status
import httpx

from collector import database, routes
from collector.settings import settings
from common.model import CollectorInfo, Position


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    with httpx.Client(base_url=settings.registry_url) as client:
        client.put(
            "/registry/collector",
            json=CollectorInfo(
                position=Position(x=settings.position_x, y=settings.position_y),
                url=settings.self_url,
            ).model_dump(),
        )
    yield
    with httpx.Client(base_url=settings.registry_url) as client:
        client.request(
            method="DELETE",
            url="/registry/collector",
            json=CollectorInfo(
                position=Position(x=settings.position_x, y=settings.position_y),
                url=settings.self_url,
            ).model_dump(),
        )


app = FastAPI(lifespan=lifespan)
app.include_router(routes.router)

@app.get(
    "/health",
    summary="Endpoint for healthcheck",
    status_code=status.HTTP_204_NO_CONTENT,
)
def health_check():
    return