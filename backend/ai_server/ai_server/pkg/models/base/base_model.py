import pandas as pd
import numpy as np
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union, cast
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')


class BaseModel(ABC):
    """
    Base class for recommendation models that can work with any tabular data.
    Supports flexible column mapping for user, item, and rating columns.
    """
    
    def __init__(self, user_col: str = 'user_id', item_col: str = 'item_id', 
                 rating_col: str = 'rating', **kwargs):
        """
        Initialize base model with flexible column mapping.
        
        :param user_col: Name of the user column
        :param item_col: Name of the item column  
        :param rating_col: Name of the rating/target column
        :param kwargs: Additional parameters for specific models
        """
        self.user_col = user_col
        self.item_col = item_col
        self.rating_col = rating_col
        
        # Encoders for categorical data
        self.user_encoder = LabelEncoder()
        self.item_encoder = LabelEncoder()
        
        # Model state
        self.is_trained = False
        self.model_params = kwargs
        
        # Data info
        self.n_users = 0
        self.n_items = 0
        self.user_mean = {}
        self.item_mean = {}
        self.global_mean = 0
        
        # Additional features
        self.feature_cols = []
        self.feature_encoders = {}
        
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare and encode the input data.
        
        :param data: Input DataFrame
        :return: Processed DataFrame
        """
        df = data.copy()
        
        # Encode user and item columns
        if self.user_col in df.columns:
            df[self.user_col + '_encoded'] = self.user_encoder.fit_transform(df[self.user_col])
        
        if self.item_col in df.columns:
            df[self.item_col + '_encoded'] = self.item_encoder.fit_transform(df[self.item_col])
        
        # Handle additional categorical features
        for col in df.columns:
            if col not in [self.user_col, self.item_col, self.rating_col] and df[col].dtype == 'object':
                if col not in self.feature_encoders:
                    self.feature_encoders[col] = LabelEncoder()
                df[col + '_encoded'] = self.feature_encoders[col].fit_transform(df[col])
                self.feature_cols.append(col)
        
        return df
    
    def _calculate_baselines(self, data: pd.DataFrame):
        """Calculate baseline statistics for recommendations."""
        if self.rating_col in data.columns:
            self.global_mean = data[self.rating_col].mean()
            self.user_mean = data.groupby(self.user_col + '_encoded')[self.rating_col].mean().to_dict()
            self.item_mean = data.groupby(self.item_col + '_encoded')[self.rating_col].mean().to_dict()
        
    def predict(self, input_data: Union[pd.DataFrame, Dict, List]) -> Union[float, List[float], np.ndarray]:
        """
        Make predictions for given input data.
        
        :param input_data: Input data (DataFrame, dict, or list)
        :return: Predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Convert input to DataFrame if needed
        if isinstance(input_data, dict):
            input_data = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            input_data = pd.DataFrame(input_data)
        
        return self._predict_impl(input_data)
    
    @abstractmethod
    def _predict_impl(self, data: pd.DataFrame) -> np.ndarray:
        """Implementation-specific prediction logic."""
        pass
    
    def train(self, training_data: pd.DataFrame):
        """
        Train the model using the provided training data.
        
        :param training_data: DataFrame with user, item, rating columns
        """
        # Prepare data
        self.training_data = self._prepare_data(training_data)
        
        # Calculate basic statistics
        self._calculate_baselines(self.training_data)
        
        # Set dimensions
        assert self.user_encoder.classes_ is not None
        assert self.item_encoder.classes_ is not None

        self.n_users = len(self.user_encoder.classes_)
        self.n_items = len(self.item_encoder.classes_)
        
        # Call implementation-specific training
        self._train_impl(self.training_data)
        
        self.is_trained = True
    
    @abstractmethod
    def _train_impl(self, data: pd.DataFrame):
        """Implementation-specific training logic."""
        pass
    
    def save(self, file_path: str):
        """
        Save the model to a file.
        
        :param file_path: Path to save the model
        """
        model_data = {
            'model_state': self.__dict__,
            'model_type': self.__class__.__name__
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, file_path: str):
        """
        Load the model from a file.
        
        :param file_path: Path to load the model from
        """
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # Restore model state
        self.__dict__.update(model_data['model_state'])
    
    def evaluate(self, test_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate the model on test data.
        
        :param test_data: Test DataFrame
        :return: Dictionary of evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Prepare test data
        test_df = test_data.copy()
        
        # Encode using existing encoders
        try:
            if self.user_col in test_df.columns:
                test_df[self.user_col + '_encoded'] = self.user_encoder.transform(test_df[self.user_col])
            
            if self.item_col in test_df.columns:
                test_df[self.item_col + '_encoded'] = self.item_encoder.transform(test_df[self.item_col])
            
            # Handle additional features
            for col in self.feature_cols:
                if col in test_df.columns:
                    test_df[col + '_encoded'] = self.feature_encoders[col].transform(test_df[col])
        
        except ValueError as e:
            print(f"Warning: Unknown categories in test data: {e}")
            return {'error': 'Unknown categories in test data'}
        
        # Make predictions
        predictions = self._predict_impl(test_df)
        
        if self.rating_col in test_df.columns:
            actual = test_df[self.rating_col].values
            
            # Calculate metrics
            mse = mean_squared_error(actual, predictions)
            mae = mean_absolute_error(actual, predictions)
            rmse = np.sqrt(mse)
            
            return {
                'mse': mse,
                'mae': mae,
                'rmse': rmse,
                'n_predictions': len(predictions)
            }
        else:
            return {
                'n_predictions': len(predictions),
                'predictions_made': True
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        :return: Dictionary containing model information
        """
        return {
            'model_type': self.__class__.__name__,
            'is_trained': self.is_trained,
            'user_col': self.user_col,
            'item_col': self.item_col,
            'rating_col': self.rating_col,
            'n_users': self.n_users,
            'n_items': self.n_items,
            'feature_cols': self.feature_cols,
            'model_params': self.model_params,
            'global_mean': self.global_mean
        }
    
    def recommend(self, user_id: Any, n_recommendations: int = 10, 
                  exclude_seen: bool = True) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a specific user.
        
        :param user_id: User identifier
        :param n_recommendations: Number of recommendations to return
        :param exclude_seen: Whether to exclude items user has already interacted with
        :return: List of recommendations with scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making recommendations")
        
        try:
            # Encode user_id
            user_encoded = self.user_encoder.transform([user_id])[0]
        except ValueError:
            # Unknown user - return popular items
            return self._get_popular_items(n_recommendations)
        
        # Get all items
        all_items = list(range(self.n_items))
        
        # Exclude seen items if requested
        if exclude_seen and hasattr(self, 'training_data'):
            seen_items = self.training_data[self.training_data[self.user_col + '_encoded'] == user_encoded
                ][self.item_col + '_encoded']
            all_items = [item for item in all_items if item not in seen_items]
        
        # Create prediction input
        prediction_input = pd.DataFrame({
            self.user_col + '_encoded': [user_encoded] * len(all_items),
            self.item_col + '_encoded': all_items
        })
        
        # Get predictions
        scores = self._predict_impl(prediction_input)
        
        # Create recommendations
        recommendations = []
        for i, (item_encoded, score) in enumerate(zip(all_items, scores)):
            # Decode item back to original
            item_original = self.item_encoder.inverse_transform([item_encoded])
            if item_original is None:
                continue
            item_original = item_original[0]
            
            recommendations.append({
                'item': item_original,
                'score': float(score),
                'rank': i + 1
            })
        
        # Sort by score and return top N
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        # Update ranks
        for i, rec in enumerate(recommendations[:n_recommendations]):
            rec['rank'] = i + 1
        
        return recommendations[:n_recommendations]
    
    def _get_popular_items(self, n_items: int) -> List[Dict[str, Any]]:
        """Get popular items as fallback recommendations."""
        if not hasattr(self, 'training_data'):
            return []
        
        # Calculate item popularity
        sizeData = cast(pd.Series, self.training_data.groupby(self.item_col + '_encoded').size())
        item_popularity = sizeData.sort_values(ascending=False)

        popular_items = []
        for i, (item_encoded, count) in enumerate(item_popularity.head(n_items).items()):
            item_original = self.item_encoder.inverse_transform([item_encoded])
            if item_original is None:
                continue
            item_original = item_original[0]
            popular_items.append({
                'item': item_original,
                'score': float(count),
                'rank': i + 1
            })
        
        return popular_items
