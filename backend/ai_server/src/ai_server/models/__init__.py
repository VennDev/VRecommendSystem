"""
Recommendation models package.

This package contains the base model architecture and specific model implementations
for the recommendation system.
"""

from .base_model import BaseRecommendationModel, ModelRegistry
from .lightfm_model import LightFMModel

__all__ = [
    'BaseRecommendationModel',
    'ModelRegistry',
    'LightFMModel'
]
