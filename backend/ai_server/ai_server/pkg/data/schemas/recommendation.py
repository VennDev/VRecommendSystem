from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List


@dataclass
class RecommendationRequest:
    user_id: str
    request_id: str
    num_recommendations: int
    filter_criteria: Dict[str, Any]
    timestamp: datetime

@dataclass
class RecommendationResult:
    request_id: str
    user_id: str
    recommendations: List[Dict[str, Any]]
    timestamp: datetime
    model_version: str
