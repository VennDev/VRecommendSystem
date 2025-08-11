from fastapi import APIRouter
from ..handlers.recommend_handler import get_recommend_handler

router = APIRouter()


@router.get("/recommend/{user_id}/{model_id}/{n}", tags=["recommendations"])
async def get_recommendations(user_id: str, model_id: str, n: int = 10):
    """
    Get recommendations for a user based on the specified model.

    Args:
        user_id (str): The ID of the user to get recommendations for.
        model_id (str): The ID of the recommendation model to use.
        n (int): The number of recommendations to return. Default is 10.
    Returns:
        dict: A dictionary containing the recommendations for the user.
    """
    return get_recommend_handler(model_id=model_id, object_id=user_id, n=n)
