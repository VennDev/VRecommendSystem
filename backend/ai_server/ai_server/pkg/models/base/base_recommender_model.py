from abc import abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging
from datetime import datetime
import pickle
import os
from .irecommender_model import IRecommenderModel


class BaseRecommenderModel(IRecommenderModel):
    """Base class implementing common functionality for all recommender models"""
    
    def __init__(self, 
                 user_col: str = "userID",
                 item_col: str = "itemID", 
                 rating_col: str = "rating",
                 timestamp_col: str = "timestamp",
                 seed: int = 42,
                 verbose: bool = True):
        """
        Initialize base recommender model
        
        Args:
            user_col: Name of user column in data
            item_col: Name of item column in data
            rating_col: Name of rating column in data
            timestamp_col: Name of timestamp column in data
            seed: Random seed for reproducibility
            verbose: Whether to print logs
        """
        self.user_col = user_col
        self.item_col = item_col
        self.rating_col = rating_col
        self.timestamp_col = timestamp_col
        self.seed = seed
        self.verbose = verbose
        
        # Model state
        self.is_fitted = False
        self.model = None
        self.user_ids = None
        self.item_ids = None
        self.n_users = None
        self.n_items = None
        
        # Metadata
        self.model_name = self.__class__.__name__
        self.created_at = datetime.now()
        self.last_trained = None
        self.training_history = []
        
        # Setup logging
        self._setup_logging()

    def check_model_state(self) -> bool:
        model = self.model is not None
        user_ids = self.user_ids is not None
        item_ids = self.item_ids is not None
        n_users = self.n_users is not None
        n_items = self.n_items is not None
        return model and user_ids and item_ids and n_users and n_items
    
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(self.model_name)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO if self.verbose else logging.WARNING)
    
    def _validate_data(self, data: pd.DataFrame, 
                      required_cols: Optional[List[str]] = None) -> None:
        """Validate input data format"""
        if required_cols is None:
            required_cols = [self.user_col, self.item_col]
        
        missing_cols = set(required_cols) - set(data.columns)
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")
        
        # Check for nulls
        null_counts = data[required_cols].isnull().sum()
        if null_counts.any():
            self.logger.warning(f"Null values found: {null_counts[null_counts > 0]}")
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Common preprocessing steps"""
        # Remove duplicates
        data = data.drop_duplicates(
            subset=[self.user_col, self.item_col], 
            keep='last'
        )
        
        # Sort by timestamp if available
        if self.timestamp_col in data.columns:
            data = data.sort_values(self.timestamp_col)
        
        return data
    
    def _extract_unique_ids(self, data: pd.DataFrame) -> None:
        """Extract and store unique user and item IDs"""
        self.user_ids = data[self.user_col].unique()
        self.item_ids = data[self.item_col].unique()
        self.n_users = len(self.user_ids)
        self.n_items = len(self.item_ids)
        
        self.logger.info(f"Found {self.n_users} users and {self.n_items} items")
    
    def fit(self, train_data: pd.DataFrame, 
            validation_data: Optional[pd.DataFrame] = None, **kwargs) -> None:
        """
        Base fit method with common preprocessing
        
        Args:
            train_data: Training data
            validation_data: Optional validation data
            **kwargs: Additional arguments for specific models
        """
        self.logger.info(f"Starting training for {self.model_name}")
        
        # Validate and preprocess
        self._validate_data(train_data)
        train_data = self._preprocess_data(train_data)
        
        # Extract unique IDs
        self._extract_unique_ids(train_data)
        
        # Store training metadata
        self.last_trained = datetime.now()
        self.training_history.append({
            'timestamp': self.last_trained,
            'n_samples': len(train_data),
            'n_users': self.n_users,
            'n_items': self.n_items
        })
        
        # Call child class implementation
        self._fit_internal(train_data, validation_data, **kwargs)
        
        self.is_fitted = True
        self.logger.info("Training completed")
    
    @abstractmethod
    def _fit_internal(self, train_data: pd.DataFrame, 
                     validation_data: Optional[pd.DataFrame] = None, **kwargs) -> None:
        """Internal fit method to be implemented by child classes"""
        pass
    
    def predict(self, test_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Base predict method with validation
        
        Args:
            test_data: Test data for predictions
            **kwargs: Additional arguments
            
        Returns:
            DataFrame with predictions
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before making predictions")
        
        self._validate_data(test_data)
        
        # Filter to known users/items
        known_mask = (
            test_data[self.user_col].isin(self.user_ids) & 
            test_data[self.item_col].isin(self.item_ids)
        )
        
        if not known_mask.all():
            self.logger.warning(
                f"Filtering out {(~known_mask).sum()} unknown user-item pairs"
            )
            test_data = test_data[known_mask]
        
        # Call child class implementation
        return self._predict_internal(test_data, **kwargs)
    
    @abstractmethod
    def _predict_internal(self, test_data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """Internal predict method to be implemented by child classes"""
        pass
    
    def recommend(self, user_ids: Optional[Union[List, np.ndarray]] = None, 
                  k: int = 10, 
                  remove_seen: bool = True,
                  **kwargs) -> Dict[Any, List[Tuple[Any, float]]]:
        """
        Generate top-k recommendations
        
        Args:
            user_ids: Users to generate recommendations for (None = all users)
            k: Number of recommendations per user
            remove_seen: Whether to remove items user has already seen
            **kwargs: Additional arguments
            
        Returns:
            Dictionary mapping user_id to list of (item_id, score) tuples
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before making recommendations")
        
        if user_ids is None:
            user_ids = self.user_ids
        
        # Validate user IDs
        user_ids = np.array(user_ids)
        unknown_users = ~np.isin(user_ids, self.user_ids)
        if unknown_users.any():
            self.logger.warning(
                f"Found {unknown_users.sum()} unknown users"
            )
            user_ids = user_ids[~unknown_users]
        
        # Call child class implementation
        return self._recommend_internal(user_ids, k, remove_seen, **kwargs)
    
    @abstractmethod
    def _recommend_internal(self, user_ids: np.ndarray, 
                           k: int, 
                           remove_seen: bool,
                           **kwargs) -> Dict[Any, List[Tuple[Any, float]]]:
        """Internal recommend method to be implemented by child classes"""
        pass
    
    def evaluate(self, test_data: pd.DataFrame, 
                 metrics: Optional[List[str]] = None,
                 k_values: List[int] = [5, 10, 20],
                 **kwargs) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            test_data: Test data for evaluation
            metrics: List of metrics to compute
            k_values: List of k values for ranking metrics
            **kwargs: Additional arguments
            
        Returns:
            Dictionary of metric names to values
        """
        if metrics is None:
            metrics = ['rmse', 'mae', 'precision', 'recall', 'ndcg']
        
        results = {}
        
        # Rating prediction metrics
        if self.rating_col in test_data.columns:
            predictions = self.predict(test_data)
            y_true = test_data[self.rating_col].values
            y_pred = predictions['prediction'].values
            
            if 'rmse' in metrics:
                results['rmse'] = np.sqrt(mean_squared_error(y_true, y_pred))
            if 'mae' in metrics:
                results['mae'] = mean_absolute_error(y_true, y_pred)
        
        # Ranking metrics
        ranking_metrics = set(metrics) & {'precision', 'recall', 'ndcg', 'map'}
        if ranking_metrics:
            # Get recommendations for all test users
            test_users = test_data[self.user_col].unique()
            recommendations = self.recommend(test_users, k=max(k_values))
            
            # Calculate metrics for each k
            for k in k_values:
                for metric in ranking_metrics:
                    score = self._calculate_ranking_metric(
                        test_data, recommendations, metric, k
                    )
                    results[f"{metric}@{k}"] = score
        
        return results
    
    def _calculate_ranking_metric(self, test_data: pd.DataFrame,
                                 recommendations: Dict,
                                 metric: str, k: int) -> float:
        """Calculate a specific ranking metric"""
        # Implementation would depend on specific metric
        # This is a placeholder
        return 0.0
    
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        self.logger.info(f"Saving model to {path}")
        
        # Create directory if needed
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save model state
        model_state = {
            'model': self.model,
            'metadata': {
                'model_name': self.model_name,
                'created_at': self.created_at,
                'last_trained': self.last_trained,
                'training_history': self.training_history,
                'user_col': self.user_col,
                'item_col': self.item_col,
                'rating_col': self.rating_col,
                'n_users': self.n_users,
                'n_items': self.n_items
            },
            'user_ids': self.user_ids,
            'item_ids': self.item_ids
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_state, f)
        
        self.logger.info("Model saved successfully")
    
    def load_model(self, path: str) -> None:
        """Load model from disk"""
        self.logger.info(f"Loading model from {path}")
        
        with open(path, 'rb') as f:
            model_state = pickle.load(f)
        
        # Restore model state
        self.model = model_state['model']
        metadata = model_state['metadata']
        
        self.model_name = metadata['model_name']
        self.created_at = metadata['created_at']
        self.last_trained = metadata['last_trained']
        self.training_history = metadata['training_history']
        self.user_col = metadata['user_col']
        self.item_col = metadata['item_col']
        self.rating_col = metadata['rating_col']
        self.n_users = metadata['n_users']
        self.n_items = metadata['n_items']
        
        self.user_ids = model_state['user_ids']
        self.item_ids = model_state['item_ids']
        
        self.is_fitted = True
        self.logger.info("Model loaded successfully")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metadata"""
        return {
            'model_name': self.model_name,
            'is_fitted': self.is_fitted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_trained': self.last_trained.isoformat() if self.last_trained else None,
            'n_users': self.n_users,
            'n_items': self.n_items,
            'training_history': self.training_history
        }
    
    def __repr__(self):
        return (f"{self.model_name}(is_fitted={self.is_fitted}, "
                f"n_users={self.n_users}, n_items={self.n_items})")
