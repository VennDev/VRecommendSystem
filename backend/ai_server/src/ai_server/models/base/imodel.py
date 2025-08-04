from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np


class IModel(ABC):
    """Interface defining the contract for all recommender models"""

    @abstractmethod
    def fit(self, train_data: pd.DataFrame, **kwargs) -> None:
        """Train the model on the given data"""
        pass

    @abstractmethod
    def predict(self, test_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Make predictions for the test data"""
        pass

    @abstractmethod
    def recommend(self, user_ids: Union[List, np.ndarray],
                  k: int = 10, **kwargs) -> Dict[Any, List[Tuple[Any, float]]]:
        """Generate top-k recommendations for given users"""
        pass

    @abstractmethod
    def evaluate(self, test_data: pd.DataFrame,
                 metrics: Optional[List[str]] = None, **kwargs) -> Dict[str, float]:
        """Evaluate model performance on test data"""
        pass

    @abstractmethod
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        pass

    @abstractmethod
    def load_model(self, path: str) -> None:
        """Load model from disk"""
        pass
