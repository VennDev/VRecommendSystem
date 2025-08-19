from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/set_running_time/{model_id}/{time}", tags=["private"])
async def set_running_time(model_id: str, time: int) -> dict:
    """
    Set the running time for a model.

    Args:
        model_id: The ID of the model to set the running time for.
        time: The running time in seconds.

    Returns:
        A dictionary confirming the running time has been set.

    Raises:
        HTTPException: If there's an error setting the running time.
    """
    try:
        # Here you would typically call a service to set the running time
        # For example, await model_service.set_running_time(model_id, time)
        return {"model_id": model_id, "running_time": time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting running time: {str(e)}") from e
