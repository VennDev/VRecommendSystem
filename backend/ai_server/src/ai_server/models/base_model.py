from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import os
import pickle
import json
import loguru


class BaseRecommendationModel(ABC):
    """
    Abstract base class for recommendation models.
    
    This class defines the common interface and functionality that all
    recommendation models should implement. It provides:
    - Common model lifecycle methods (fit, predict, save, load)
    - Standardized data validation
    - Metrics tracking
    - Model metadata management
    - Error handling patterns
    """

    def __init__(self, model_id: str = None, **hyperparameters):
        """
        Initialize the base recommendation model.
        
        Args:
            model_id: Unique identifier for the model
            **hyperparameters: Model-specific hyperparameters
        """
        self.model_id = model_id or f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.hyperparameters = hyperparameters
        self.is_fitted = False
        self.metrics = {}
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'model_type': self.__class__.__name__,
            'version': '1.0.0'
        }

        # Data mappings for ID conversion
        self.user_id_mapping = {}
        self.item_id_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_item_mapping = {}

        # Training data statistics
        self.training_stats = {}

        # Model-specific attributes (to be set by subclasses)
        self.model = None

    @abstractmethod
    def fit(self,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            **kwargs) -> 'BaseRecommendationModel':
        """
        Train the recommendation model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id', 'rating']
            user_features: Optional DataFrame with user features
            item_features: Optional DataFrame with item features
            **kwargs: Additional training parameters
            
        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def predict(self,
                user_ids: List[str],
                n_recommendations: int = 10,
                **kwargs) -> pd.DataFrame:
        """
        Generate recommendations for users.
        
        Args:
            user_ids: List of user IDs to generate recommendations for
            n_recommendations: Number of recommendations per user
            **kwargs: Additional prediction parameters
            
        Returns:
            DataFrame with columns ['user_id', 'item_id', 'score']
        """
        pass

    @abstractmethod
    def predict_score(self,
                      user_ids: List[str],
                      item_ids: List[str]) -> List[float]:
        """
        Predict scores for specific user-item pairs.
        
        Args:
            user_ids: List of user IDs
            item_ids: List of item IDs (same length as user_ids)
            
        Returns:
            List of predicted scores
        """
        pass

    def validate_interaction_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean interaction data.
        
        Args:
            data: Raw interaction data
            
        Returns:
            Cleaned interaction data
            
        Raises:
            ValueError: If data is invalid
        """
        if data.empty:
            raise ValueError("Interaction data cannot be empty")

        required_columns = ['user_id', 'item_id']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Create a copy to avoid modifying original data
        cleaned_data = data.copy()

        # Ensure string IDs
        cleaned_data['user_id'] = cleaned_data['user_id'].astype(str)
        cleaned_data['item_id'] = cleaned_data['item_id'].astype(str)

        # Handle ratings
        if 'rating' in cleaned_data.columns:
            cleaned_data['rating'] = pd.to_numeric(cleaned_data['rating'], errors='coerce')
            # Fill NaN ratings with default value
            cleaned_data['rating'] = cleaned_data['rating'].fillna(1.0)
        else:
            # Add default rating if not present
            cleaned_data['rating'] = 1.0

        # Remove rows with NaN in critical columns
        cleaned_data = cleaned_data.dropna(subset=['user_id', 'item_id'])

        # Remove duplicates
        cleaned_data = cleaned_data.drop_duplicates(subset=['user_id', 'item_id'])

        if cleaned_data.empty:
            raise ValueError("No valid interactions after cleaning")

        return cleaned_data.reset_index(drop=True)

    def validate_feature_data(self, data: pd.DataFrame, feature_type: str) -> pd.DataFrame:
        """
        Validate and clean feature data.
        
        Args:
            data: Raw feature data
            feature_type: Either 'user' or 'item'
            
        Returns:
            Cleaned feature data
        """
        if data.empty:
            return data

        id_column = f'{feature_type}_id'
        if id_column not in data.columns:
            raise ValueError(f"Feature data must contain '{id_column}' column")

        cleaned_data = data.copy()
        cleaned_data[id_column] = cleaned_data[id_column].astype(str)

        # Remove duplicates based on ID
        cleaned_data = cleaned_data.drop_duplicates(subset=[id_column])

        return cleaned_data.reset_index(drop=True)

    def build_id_mappings(self, interaction_data: pd.DataFrame):
        """
        Build mappings between string IDs and integer indices.
        
        Args:
            interaction_data: Cleaned interaction data
        """
        unique_users = sorted(interaction_data['user_id'].unique())
        unique_items = sorted(interaction_data['item_id'].unique())

        self.user_id_mapping = {user_id: idx for idx, user_id in enumerate(unique_users)}
        self.item_id_mapping = {item_id: idx for idx, item_id in enumerate(unique_items)}

        self.reverse_user_mapping = {idx: user_id for user_id, idx in self.user_id_mapping.items()}
        self.reverse_item_mapping = {idx: item_id for item_id, idx in self.item_id_mapping.items()}

    def calculate_training_stats(self, interaction_data: pd.DataFrame):
        """
        Calculate and store training statistics.
        
        Args:
            interaction_data: Training interaction data
        """
        n_users = len(interaction_data['user_id'].unique())
        n_items = len(interaction_data['item_id'].unique())
        n_interactions = len(interaction_data)

        # Calculate sparsity
        sparsity = 1 - (n_interactions / (n_users * n_items))

        # Rating statistics
        rating_stats = {}
        if 'rating' in interaction_data.columns:
            rating_stats = {
                'mean_rating': float(interaction_data['rating'].mean()),
                'std_rating': float(interaction_data['rating'].std()),
                'min_rating': float(interaction_data['rating'].min()),
                'max_rating': float(interaction_data['rating'].max())
            }

        self.training_stats = {
            'n_users': n_users,
            'n_items': n_items,
            'n_interactions': n_interactions,
            'sparsity': sparsity,
            'density': 1 - sparsity,
            'avg_interactions_per_user': n_interactions / n_users,
            'avg_interactions_per_item': n_interactions / n_items,
            **rating_stats
        }

    def update_metrics(self, new_metrics: Dict[str, Any]):
        """
        Update model metrics.
        
        Args:
            new_metrics: Dictionary of new metrics to add/update
        """
        self.metrics.update(new_metrics)
        self.metadata['last_updated'] = datetime.now().isoformat()

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get comprehensive model information.
        
        Returns:
            Dictionary containing model metadata, stats, and metrics
        """
        return {
            'model_id': self.model_id,
            'model_type': self.__class__.__name__,
            'is_fitted': self.is_fitted,
            'hyperparameters': self.hyperparameters,
            'metadata': self.metadata,
            'training_stats': self.training_stats,
            'metrics': self.metrics,
            'n_users': len(self.user_id_mapping),
            'n_items': len(self.item_id_mapping)
        }

    def save(self, filepath: str):
        """
        Save the model to disk.
        
        Args:
            filepath: Path to save the model
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Prepare data to save
        model_data = {
            'model_id': self.model_id,
            'model_type': self.__class__.__name__,
            'hyperparameters': self.hyperparameters,
            'is_fitted': self.is_fitted,
            'metrics': self.metrics,
            'metadata': self.metadata,
            'training_stats': self.training_stats,
            'user_id_mapping': self.user_id_mapping,
            'item_id_mapping': self.item_id_mapping,
            'reverse_user_mapping': self.reverse_user_mapping,
            'reverse_item_mapping': self.reverse_item_mapping,
            'model': self.model  # Model-specific data
        }

        # Add any additional model-specific data
        additional_data = self._get_save_data()
        model_data.update(additional_data)

        # Save to a pickle file
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        # Save metadata as JSON for easy inspection
        metadata_path = filepath.replace('.pkl', '_metadata.json')
        metadata = {
            'model_id': self.model_id,
            'model_type': self.__class__.__name__,
            'saved_at': datetime.now().isoformat(),
            'file_path': filepath,
            'hyperparameters': self.hyperparameters,
            'training_stats': self.training_stats,
            'metrics': self.metrics
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        loguru.logger.info(f"Model {self.model_id} saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'BaseRecommendationModel':
        """
        Load a model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded model instance
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        # Create instance with saved hyperparameters
        instance = cls(
            model_id=model_data['model_id'],
            **model_data['hyperparameters']
        )

        # Restore state
        instance.is_fitted = model_data['is_fitted']
        instance.metrics = model_data['metrics']
        instance.metadata = model_data['metadata']
        instance.training_stats = model_data['training_stats']
        instance.user_id_mapping = model_data['user_id_mapping']
        instance.item_id_mapping = model_data['item_id_mapping']
        instance.reverse_user_mapping = model_data['reverse_user_mapping']
        instance.reverse_item_mapping = model_data['reverse_item_mapping']
        instance.model = model_data['model']

        # Load any additional model-specific data
        instance._load_additional_data(model_data)

        loguru.logger.info(f"Model {instance.model_id} loaded from {filepath}")
        return instance

    def _get_save_data(self) -> Dict[str, Any]:
        """
        Get additional data to save (to be overridden by subclasses).
        
        Returns:
            Dictionary of additional data to save
        """
        return {}

    def _load_additional_data(self, model_data: Dict[str, Any]):
        """
        Load additional data (to be overridden by subclasses).
        
        Args:
            model_data: Dictionary containing saved model data
        """
        pass

    def evaluate(self,
                 test_data: pd.DataFrame,
                 metrics: List[str] = None,
                 k_values: List[int] = None) -> Dict[str, float]:
        """
        Evaluate the model on test data.
        
        Args:
            test_data: Test interaction data
            metrics: List of metrics to calculate
            k_values: List of k values for ranking metrics
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")

        if metrics is None:
            metrics = ['precision', 'recall', 'ndcg']

        if k_values is None:
            k_values = [5, 10, 20]

        # This is a basic implementation - subclasses should override for specific metrics
        return self._calculate_metrics(test_data, metrics, k_values)

    def _calculate_metrics(self,
                           test_data: pd.DataFrame,
                           metrics: List[str],
                           k_values: List[int]) -> Dict[str, float]:
        """
        Calculate evaluation metrics (to be implemented by subclasses).
        
        Args:
            test_data: Test data
            metrics: Metrics to calculate
            k_values: K values for ranking metrics
            
        Returns:
            Dictionary of calculated metrics
        """
        # Basic implementation - subclasses should provide specific implementations
        return {}

    def get_user_recommendations(self,
                                 user_id: str,
                                 n_recommendations: int = 10,
                                 exclude_seen: bool = True) -> List[Dict[str, Any]]:
        """
        Get recommendations for a single user.
        
        Args:
            user_id: User ID to get recommendations for
            n_recommendations: Number of recommendations
            exclude_seen: Whether to exclude items the user has already interacted with
            
        Returns:
            List of recommendation dictionaries
        """
        predictions_df = self.predict([user_id], n_recommendations)

        recommendations = []
        for _, row in predictions_df.iterrows():
            if row['user_id'] == user_id:
                recommendations.append({
                    'item_id': row['item_id'],
                    'score': float(row['score']),
                    'rank': len(recommendations) + 1
                })

        return recommendations

    def get_similar_items(self,
                          item_id: str,
                          n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Get items similar to a given item (to be implemented by subclasses).
        
        Args:
            item_id: Item ID to find similar items for
            n_similar: Number of similar items to return
            
        Returns:
            List of similar item dictionaries
        """
        # Default implementation - subclasses should override
        return []

    def get_similar_users(self,
                          user_id: str,
                          n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Get users similar to a given user (to be implemented by subclasses).
        
        Args:
            user_id: User ID to find similar users for
            n_similar: Number of similar users to return
            
        Returns:
            List of similar user dictionaries
        """
        # Default implementation - subclasses should override
        return []

    def __str__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(model_id='{self.model_id}', fitted={self.is_fitted})"

    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return (f"{self.__class__.__name__}("
                f"model_id='{self.model_id}', "
                f"fitted={self.is_fitted}, "
                f"n_users={len(self.user_id_mapping)}, "
                f"n_items={len(self.item_id_mapping)})")


class ModelRegistry:
    """
    Registry for managing different recommendation model types.
    """

    _models = {}

    @classmethod
    def register(cls, name: str, model_class: type):
        """
        Register a model class.
        
        Args:
            name: Name to register the model under
            model_class: Model class to register
        """
        if not issubclass(model_class, BaseRecommendationModel):
            raise ValueError("Model class must inherit from BaseRecommendationModel")

        cls._models[name] = model_class
        loguru.logger.info(f"Registered model: {name}")

    @classmethod
    def get_model(cls, name: str) -> type:
        """
        Get a registered model class.
        
        Args:
            name: Name of the model to get
            
        Returns:
            Model class
        """
        if name not in cls._models:
            raise ValueError(f"Model '{name}' not registered. Available models: {list(cls._models.keys())}")

        return cls._models[name]

    @classmethod
    def list_models(cls) -> List[str]:
        """
        List all registered model names.
        
        Returns:
            List of registered model names
        """
        return list(cls._models.keys())

    @classmethod
    def create_model(cls, name: str, **kwargs) -> BaseRecommendationModel:
        """
        Create an instance of a registered model.
        
        Args:
            name: Name of the model to create
            **kwargs: Arguments to pass to the model constructor
            
        Returns:
            Model instance
        """
        model_class = cls.get_model(name)
        return model_class(**kwargs)
