import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, Any, List
from ..base.base_model import BaseModel


class MatrixFactorizationModel(BaseModel):
    """
    Matrix Factorization model using Non-negative Matrix Factorization (NMF).
    Can work with any tabular data by treating it as user-item interactions.
    """

    def __init__(self, user_col: str = 'user_id', item_col: str = 'item_id', 
                 rating_col: str = 'rating', n_factors: int = 50, 
                 max_iter: int = 200, regularization: float = 0.01, **kwargs):
        """
        Initialize Matrix Factorization model.
        
        :param user_col: Name of the user column
        :param item_col: Name of the item column
        :param rating_col: Name of the rating/target column
        :param n_factors: Number of latent factors
        :param max_iter: Maximum number of iterations
        :param regularization: Regularization parameter
        """
        super().__init__(user_col, item_col, rating_col, **kwargs)
        
        self.n_factors = n_factors
        self.max_iter = max_iter
        self.regularization = regularization
        
        # Model components
        self.nmf_model = None
        self.user_factors = None
        self.item_factors = None
        self.rating_matrix = None
        self.rating_scaler = MinMaxScaler()
        
        # Store for prediction
        self.min_rating = 0
        self.max_rating = 5
        
    def _create_rating_matrix(self, data: pd.DataFrame) -> csr_matrix:
        """
        Create user-item rating matrix from DataFrame.
        
        :param data: Input DataFrame
        :return: Sparse rating matrix
        """
        # Create pivot table
        rating_matrix = data.pivot_table(
            index=self.user_col + '_encoded',
            columns=self.item_col + '_encoded',
            values=self.rating_col,
            fill_value=0
        )
        
        # Store rating bounds
        ratings = data[self.rating_col].to_numpy()
        self.min_rating = ratings.min()
        self.max_rating = ratings.max()
        
        # Scale ratings to [0, 1] for NMF
        rating_values = rating_matrix.values
        rating_values_scaled = self.rating_scaler.fit_transform(rating_values)
        
        # Convert to sparse matrix
        self.rating_matrix = csr_matrix(rating_values_scaled)
        
        return self.rating_matrix
    
    def _train_impl(self, data: pd.DataFrame):
        """
        Train the Matrix Factorization model.
        
        :param data: Training data
        """
        # Create rating matrix
        rating_matrix = self._create_rating_matrix(data)
        
        # Initialize and train NMF
        self.nmf_model = NMF(
            n_components=str(self.n_factors),
            max_iter=self.max_iter,
            alpha_H=str(self.regularization),
            alpha_W=self.regularization,
            random_state=42,
            init='nndsvd'
        )
        
        # Fit the model
        self.user_factors = self.nmf_model.fit_transform(rating_matrix)
        self.item_factors = self.nmf_model.components_
        
        print(f"Matrix Factorization trained with {self.n_factors} factors")
        print(f"User factors shape: {self.user_factors.shape}")
        print(f"Item factors shape: {self.item_factors.shape}")
    
    def _predict_impl(self, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        :param data: Input data for prediction
        :return: Predicted ratings
        """
        predictions = []
        
        for _, row in data.iterrows():
            user_encoded = row[self.user_col + '_encoded']
            item_encoded = row[self.item_col + '_encoded']
            
            # Handle out-of-bounds users/items
            if user_encoded >= self.n_users or item_encoded >= self.n_items:
                # Use global mean for unknown users/items
                pred = self.global_mean
            else:
                if self.nmf_model is None:
                    raise ValueError("Model must be trained first")

                if self.user_factors is None or self.item_factors is None:
                    raise ValueError("User or item factors are not initialized")

                # Matrix factorization prediction
                pred_scaled = np.dot(self.user_factors[user_encoded], 
                                   self.item_factors[:, item_encoded])
                
                # Scale back to original range
                pred_scaled = np.array([[pred_scaled]])
                pred = self.rating_scaler.inverse_transform(pred_scaled)[0, 0]
            
            # Clip to rating bounds
            pred = np.clip(pred, self.min_rating, self.max_rating)
            predictions.append(pred)
        
        return np.array(predictions)
    
    def get_user_factors(self, user_id: Any) -> np.ndarray:
        """
        Get latent factors for a specific user.
        
        :param user_id: User identifier
        :return: User factor vector
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if self.user_factors is None:
                raise ValueError("User factors are not initialized")

        try:
            user_encoded = self.user_encoder.transform([user_id])[0]
            return self.user_factors[user_encoded]
        except (ValueError, IndexError):
            # Return mean user factors for unknown users
            return np.mean(self.user_factors, axis=0)
    
    def get_item_factors(self, item_id: Any) -> np.ndarray:
        """
        Get latent factors for a specific item.
        
        :param item_id: Item identifier
        :return: Item factor vector
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if self.item_factors is None:
            raise ValueError("Item factors are not initialized")
        
        try:
            item_encoded = self.item_encoder.transform([item_id])[0]
            return self.item_factors[:, item_encoded]
        except (ValueError, IndexError):
            # Return mean item factors for unknown items
            return np.mean(self.item_factors, axis=1)
    
    def find_similar_users(self, user_id: Any, n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar users based on latent factors.
        
        :param user_id: Target user
        :param n_similar: Number of similar users to return
        :return: List of similar users with similarity scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if self.user_factors is None:
            raise ValueError("User factors are not initialized")
        
        try:
            user_encoded = self.user_encoder.transform([user_id])[0]
            target_factors = self.user_factors[user_encoded]
        except (ValueError, IndexError):
            return []
        
        # Calculate cosine similarity with all users
        similarities = []
        for u in range(self.n_users):
            if u != user_encoded:
                similarity = np.dot(target_factors, self.user_factors[u]) / (
                    np.linalg.norm(target_factors) * np.linalg.norm(self.user_factors[u]) + 1e-10
                )
                
                # Get original user ID
                original_user = self.user_encoder.inverse_transform([u])
                if original_user is None:
                    continue
                original_user = original_user[0]

                similarities.append({
                    'user': original_user,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:n_similar]
    
    def find_similar_items(self, item_id: Any, n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar items based on latent factors.
        
        :param item_id: Target item
        :param n_similar: Number of similar items to return
        :return: List of similar items with similarity scores
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if self.item_factors is None:
            raise ValueError("Item factors are not initialized")
        
        try:
            item_encoded = self.item_encoder.transform([item_id])[0]
            target_factors = self.item_factors[:, item_encoded]
        except (ValueError, IndexError):
            return []
        
        # Calculate cosine similarity with all items
        similarities = []
        for i in range(self.n_items):
            if i != item_encoded:
                similarity = np.dot(target_factors, self.item_factors[:, i]) / (
                    np.linalg.norm(target_factors) * np.linalg.norm(self.item_factors[:, i]) + 1e-10
                )
                
                # Get original item ID
                original_item = self.item_encoder.inverse_transform([i])
                if original_item is None:
                    continue
                original_item = original_item[0]

                similarities.append({
                    'item': original_item,
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and return top N
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:n_similar]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        base_info = super().get_model_info()
        
        mf_info = {
            'n_factors': self.n_factors,
            'max_iter': self.max_iter,
            'regularization': self.regularization,
            'min_rating': self.min_rating,
            'max_rating': self.max_rating,
            'reconstruction_error': float(self.nmf_model.reconstruction_err_) if self.nmf_model else None
        }
        
        base_info.update(mf_info)
        return base_info
    
    def explain_prediction(self, user_id: Any, item_id: Any) -> Dict[str, Any]:
        """
        Explain why a particular prediction was made.
        
        :param user_id: User identifier
        :param item_id: Item identifier
        :return: Explanation details
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        if self.user_factors is None or self.item_factors is None:
            raise ValueError("User or item factors are not initialized")
        
        try:
            user_encoded = self.user_encoder.transform([user_id])[0]
            item_encoded = self.item_encoder.transform([item_id])[0]
            
            user_factors = self.user_factors[user_encoded]
            item_factors = self.item_factors[:, item_encoded]
            
            # Calculate factor contributions
            contributions = user_factors * item_factors
            
            # Get prediction
            prediction_input = pd.DataFrame({
                self.user_col + '_encoded': [user_encoded],
                self.item_col + '_encoded': [item_encoded]
            })
            
            prediction = self._predict_impl(prediction_input)[0]
            
            return {
                'user_id': user_id,
                'item_id': item_id,
                'prediction': float(prediction),
                'user_factors': user_factors.tolist(),
                'item_factors': item_factors.tolist(),
                'factor_contributions': contributions.tolist(),
                'top_factors': sorted(enumerate(contributions), key=lambda x: abs(x[1]), reverse=True)[:5]
            }
        
        except (ValueError, IndexError):
            return {
                'user_id': user_id,
                'item_id': item_id,
                'prediction': float(self.global_mean),
                'explanation': 'Unknown user or item, using global mean'
            }
