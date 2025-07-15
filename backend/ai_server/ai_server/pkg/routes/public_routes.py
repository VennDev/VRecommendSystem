from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter(tags=["api"], prefix="/api/v1")

@router.get("/ping")
def ping(request: Request):
    client_ip = request.client.host
    logger.info(f"Ping endpoint called from ip: {client_ip}")
    return {"message": "pong"}
