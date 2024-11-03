import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, status

from producer import routes
from producer.service import process_orders_routine

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(process_orders_routine())
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(routes.router)

@app.get(
    "/health",
    summary="Endpoint for healthcheck",
    status_code=status.HTTP_204_NO_CONTENT,
)
def health_check():
    return