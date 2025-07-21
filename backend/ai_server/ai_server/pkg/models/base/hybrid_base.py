from typing import List
from .base_recommender_model import BaseRecommenderModel

class HybridBase(BaseRecommenderModel):
    """Base class for hybrid recommender models"""
    
    def __init__(self,
                 models: List[BaseRecommenderModel],
                 weights: List[float],
                 **kwargs):
        super().__init__(**kwargs)
        self.models = models or []
        self.weights = weights or [1.0] * len(self.models)
        
        if len(self.models) != len(self.weights):
            raise ValueError("Number of models must match number of weights")
        
        # Normalize weights
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
    
    def add_model(self, model: BaseRecommenderModel, weight: float = 1.0):
        """Add a model to the hybrid ensemble"""
        self.models.append(model)
        self.weights.append(weight)
        
        # Re-normalize weights
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
