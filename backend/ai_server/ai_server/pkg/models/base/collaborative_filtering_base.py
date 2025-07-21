import pandas as pd
from .base_recommender_model import BaseRecommenderModel

class CollaborativeFilteringBase(BaseRecommenderModel):
    """Base class for collaborative filtering models"""
    
    def __init__(self, 
                 n_factors: int = 50,
                 regularization: float = 0.01,
                 **kwargs):
        super().__init__(**kwargs)
        self.n_factors = n_factors
        self.regularization = regularization
        self.user_factors = None
        self.item_factors = None
    
    def _create_user_item_matrix(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create user-item interaction matrix"""
        return data.pivot(
            index=self.user_col,
            columns=self.item_col,
            values=self.rating_col
        ).fillna(0)
