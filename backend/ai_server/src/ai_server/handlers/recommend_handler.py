from typing import Dict
from ..services.model_service import ModelService


def get_recommend_handler(model_id: str, object_id: str, n: int = 10) -> Dict[str, any]:
    """
    Handle recommendation requests.
    Args:
        object_id: ID of the object to recommend
        model_id: ID of the recommendation model
    Returns:
        dict: Recommendation results
    """
    predictions = ModelService().predict_with_model(
        model_id=model_id, user_id=object_id, top_k=n
    )
    return predictions
