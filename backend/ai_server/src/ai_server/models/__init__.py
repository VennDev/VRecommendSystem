"""
Recommendation models package.

This package contains the base model architecture and specific model implementations
for the recommendation system.
"""

from .base_model import BaseRecommendationModel, ModelRegistry
from .svd_model import SVDRecommendationModel
from .nmf_model import NMFRecommendationModel

__all__ = [
    'BaseRecommendationModel',
    'ModelRegistry',
    'SVDRecommendationModel',
    'NMFRecommendationModel'
]
