import asyncio
from typing import Dict
from ..services.model_service import ModelService


async def get_recommend_handler(
    model_id: str, object_id: str, n: int = 10
) -> Dict[str, any]:
    """
    Handle recommendation requests.
    Args:
        object_id: ID of the object to recommend
        model_id: ID of the recommendation model
        n: Number of recommendations to return
    Returns:
        dict: Recommendation results
    """
    loop = asyncio.get_event_loop()
    prediction = await loop.run_in_executor(
        None, ModelService().predict_recommendations, model_id, object_id, n
    )
    return prediction.to_dict()
