from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter(tags=["api"], prefix="/api/v1")

@router.get("/ping")
def ping(request: Request):
    client = request.client
    if client is None:
        logger.warning("Ping endpoint called without a client IP.")
        return {"message": "pong"}

    client_ip = client.host
    logger.info(f"Ping endpoint called from ip: {client_ip}")
    return {"message": "pong"}
