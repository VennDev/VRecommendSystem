"""
Base recommender class that all recommendation models inherit from.
Provides a consistent API for training, prediction, and model persistence.
"""

import pandas as pd
import numpy as np
import pickle
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, cast
import os
from datetime import datetime

from python_multipart.decoders import SupportsWrite


class BaseRecommender(ABC):
    """
    Abstract base class for all recommendation models.

    Provides a scikit-learn style API with fit, predict, save, and load methods.
    All models work with pandas DataFrames as input.
    """

    def __init__(self, **kwargs):
        """
        Initialize the base recommender.

        Args:
            **kwargs: Model-specific hyperparameters
        """
        self.hyperparameters = kwargs
        self.is_fitted = False
        self.user_encoder = None
        self.item_encoder = None
        self.model = None
        self.training_history = []
        self.metrics = {}

    @abstractmethod
    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'BaseRecommender':
        """
        Train the recommendation model.

        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id', 'rating']
            user_features: Optional DataFrame with user features
            item_features: Optional DataFrame with item features

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def predict(self, user_ids: Union[List, np.ndarray, str],
                n_recommendations: int = 10) -> pd.DataFrame:
        """
        Generate recommendations for users.

        Args:
            user_ids: Single user ID or list of user IDs
            n_recommendations: Number of recommendations per user

        Returns:
            DataFrame with columns ['user_id', 'item_id', 'score']
        """
        pass

    def predict_score(self, user_ids: Union[List, str],
                      item_ids: Union[List, str]) -> np.ndarray:
        """
        Predict scores for specific user-item pairs.

        Args:
            user_ids: User IDs
            item_ids: Item IDs

        Returns:
            Array of predicted scores
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")

        # Default implementation - subclasses should override for efficiency
        if isinstance(user_ids, str):
            user_ids = [user_ids]
        if isinstance(item_ids, str):
            item_ids = [item_ids]

        scores = []
        for user_id, item_id in zip(user_ids, item_ids):
            user_recs = self.predict([user_id], n_recommendations=1000)
            item_score = user_recs[user_recs['item_id'] == item_id]
            if len(item_score) > 0:
                scores.append(item_score['score'].iloc[0])
            else:
                scores.append(0.0)

        return np.array(scores)

    def save(self, filepath: str) -> None:
        """
        Save the trained model to disk.

        Args:
            filepath: Path where to save the model
        """
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model")

        model_data = {
            'model': self.model,
            'hyperparameters': self.hyperparameters,
            'user_encoder': self.user_encoder,
            'item_encoder': self.item_encoder,
            'is_fitted': self.is_fitted,
            'training_history': self.training_history,
            'metrics': self.metrics,
            'model_type': self.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, cast(SupportsWrite[bytes], f))

    @classmethod
    def load(cls, filepath: str) -> 'BaseRecommender':
        """
        Load a trained model from disk.

        Args:
            filepath: Path to the saved model

        Returns:
            Loaded model instance
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        # Create instance
        instance = cls(**model_data['hyperparameters'])

        # Restore state
        instance.model = model_data['model']
        instance.user_encoder = model_data['user_encoder']
        instance.item_encoder = model_data['item_encoder']
        instance.is_fitted = model_data['is_fitted']
        instance.training_history = model_data['training_history']
        instance.metrics = model_data['metrics']

        return instance

    def get_hyperparameters(self) -> Dict[str, Any]:
        """Get model hyperparameters."""
        return self.hyperparameters.copy()

    def get_metrics(self) -> Dict[str, float]:
        """Get training metrics."""
        return self.metrics.copy()

    def _encode_users_items(self, interaction_data: pd.DataFrame) -> pd.DataFrame:
        """
        Encode user and item IDs to integer indices.

        Args:
            interaction_data: DataFrame with user_id and item_id columns

        Returns:
            DataFrame with encoded user_idx and item_idx columns
        """
        from sklearn.preprocessing import LabelEncoder

        if self.user_encoder is None:
            self.user_encoder = LabelEncoder()
            interaction_data['user_idx'] = self.user_encoder.fit_transform(interaction_data['user_id'])
        else:
            interaction_data['user_idx'] = self.user_encoder.transform(interaction_data['user_id'])

        if self.item_encoder is None:
            self.item_encoder = LabelEncoder()
            interaction_data['item_idx'] = self.item_encoder.fit_transform(interaction_data['item_id'])
        else:
            interaction_data['item_idx'] = self.item_encoder.transform(interaction_data['item_id'])

        return interaction_data

    def _validate_input(self, interaction_data: pd.DataFrame) -> None:
        """
        Validate input DataFrame format.

        Args:
            interaction_data: Input DataFrame to validate
        """
        required_columns = ['user_id', 'item_id']

        if not all(col in interaction_data.columns for col in required_columns):
            raise ValueError(f"Input data must contain columns: {required_columns}")

        if interaction_data.empty:
            raise ValueError("Input data cannot be empty")

        if interaction_data.isnull().any().any():
            raise ValueError("Input data contains null values")

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(fitted={self.is_fitted})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        params_str = ", ".join([f"{k}={v}" for k, v in self.hyperparameters.items()])
        return f"{self.__class__.__name__}({params_str})"
