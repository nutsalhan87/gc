from fastapi import FastAPI, status

from registry import routes


app = FastAPI()
app.include_router(routes.router)


@app.get(
    "/health",
    summary="Endpoint for healthcheck",
    status_code=status.HTTP_204_NO_CONTENT,
)
def health_check():
    return
