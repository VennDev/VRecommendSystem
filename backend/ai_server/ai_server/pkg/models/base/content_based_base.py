import pandas as pd
from abc import ABC, abstractmethod
from .base_recommender_model import BaseRecommenderModel

class ContentBasedBase(BaseRecommenderModel):
    """Base class for content-based recommender models"""
    
    def __init__(self,
                 item_features: pd.DataFrame,
                 user_features: pd.DataFrame,
                 **kwargs):
        super().__init__(**kwargs)
        self.item_features = item_features
        self.user_features = user_features
        self.item_profiles = None
        self.user_profiles = None
    
    def _validate_features(self):
        """Validate feature data"""
        if self.item_features is not None:
            if self.item_col not in self.item_features.columns:
                raise ValueError(f"Item features must contain {self.item_col}")
        
        if self.user_features is not None:
            if self.user_col not in self.user_features.columns:
                raise ValueError(f"User features must contain {self.user_col}")
