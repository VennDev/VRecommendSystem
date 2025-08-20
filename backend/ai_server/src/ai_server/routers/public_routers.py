"""
Public API routers for recommendation endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..handlers.recommend_handler import get_recommend_handler

router = APIRouter()


@router.get("/recommend/{user_id}/{model_id}/{n}", tags=["recommendations"])
async def get_recommendations(
        user_id: str, model_id: str, n: int = 10
) -> Dict[str, Any]:
    """
    Get recommendations for a user based on the specified model.

    Args:
        user_id: The ID of the user to get recommendations for.
        model_id: The ID of the recommendation model to use.
        n: The number of recommendations to return. Default is 10.

    Returns:
        Dictionary containing the recommendations for the user.

    Raises:
        HTTPException: If there's an error getting recommendations.
    """
    try:
        return await get_recommend_handler(model_id=model_id, object_id=user_id, n=n)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting recommendations: {str(e)}"
        ) from e


@router.get("/recommend/{user_id}/{model_id}", tags=["recommendations"])
async def get_recommendations_default(user_id: str, model_id: str) -> Dict[str, Any]:
    """
    Get recommendations for a user with default count (10).

    Args:
        user_id: The ID of the user to get recommendations for.
        model_id: The ID of the recommendation model to use.

    Returns:
        Dictionary containing the recommendations for the user.

    Raises:
        HTTPException: If there's an error getting recommendations.
    """
    return await get_recommendations(user_id=user_id, model_id=model_id, n=10)
