from fastapi import APIRouter

router = APIRouter(tags=["api"], prefix="/api/v1")

@router.get("/ping")
def ping():
    """
    Endpoint to check if the server is running.
    """
    return {"message": "pong"}