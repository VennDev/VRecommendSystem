"""
Alternating Least Squares (ALS) Collaborative Filtering Implementation
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List
from scipy.sparse import csr_matrix
from sklearn.metrics import mean_squared_error
import time

from ..base_model import BaseRecommender


class ALSRecommender(BaseRecommender):
    """
    Alternating Least Squares matrix factorization for collaborative filtering.
    
    This implementation uses explicit feedback and optimizes the following objective:
    min ||R - U * V^T||_F^2 + lambda * (||U||_F^2 + ||V||_F^2)
    
    Parameters:
    -----------
    factors : int, default=100
        Number of latent factors
    regularization : float, default=0.01
        Regularization parameter
    iterations : int, default=15
        Number of ALS iterations
    random_state : int, default=42
        Random seed for reproducibility
    """

    def __init__(self, factors: int = 100, regularization: float = 0.01,
                 iterations: int = 15, random_state: int = 42, **kwargs):
        super().__init__(factors=factors, regularization=regularization,
                         iterations=iterations, random_state=random_state, **kwargs)

        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.random_state = random_state

        self.user_factors = None
        self.item_factors = None
        self.global_mean = None

    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'ALSRecommender':
        """
        Train the ALS model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id', 'rating']
            user_features: Not used in ALS (for API consistency)
            item_features: Not used in ALS (for API consistency)
            
        Returns:
            Self for method chaining
        """
        self._validate_input(interaction_data)

        if 'rating' not in interaction_data.columns:
            raise ValueError("ALS requires 'rating' column for explicit feedback")

        print(f"Training ALS model with {len(interaction_data)} interactions...")
        start_time = time.time()

        # Encode users and items
        data = self._encode_users_items(interaction_data.copy())

        # Create user-item rating matrix
        self.n_users = len(self.user_encoder.classes_)
        self.n_items = len(self.item_encoder.classes_)

        # Create sparse rating matrix
        rating_matrix = csr_matrix(
            (data['rating'].values, (data['user_idx'].values, data['item_idx'].values)),
            shape=(self.n_users, self.n_items)
        )

        self.global_mean = data['rating'].mean()

        # Initialize factors
        np.random.seed(self.random_state)
        self.user_factors = np.random.normal(
            scale=1.0 / self.factors, size=(self.n_users, self.factors)
        )
        self.item_factors = np.random.normal(
            scale=1.0 / self.factors, size=(self.n_items, self.factors)
        )

        # ALS training loop
        for iteration in range(self.iterations):
            # Update user factors
            self._update_user_factors(rating_matrix)

            # Update item factors  
            self._update_item_factors(rating_matrix)

            # Calculate and log training loss
            if iteration % 5 == 0:
                rmse = self._calculate_rmse(rating_matrix)
                print(f"Iteration {iteration}: RMSE = {rmse:.4f}")
                self.training_history.append({'iteration': iteration, 'rmse': rmse})

        # Final metrics
        final_rmse = self._calculate_rmse(rating_matrix)
        training_time = time.time() - start_time

        self.metrics = {
            'final_rmse': final_rmse,
            'training_time': training_time,
            'iterations': self.iterations,
            'n_users': self.n_users,
            'n_items': self.n_items
        }

        self.is_fitted = True
        print(f"Training completed in {training_time:.2f}s. Final RMSE: {final_rmse:.4f}")

        return self

    def _update_user_factors(self, rating_matrix: csr_matrix) -> None:
        """Update user factors using least squares."""
        YtY = self.item_factors.T.dot(self.item_factors)
        regularization_diag = np.eye(self.factors) * self.regularization

        for user_idx in range(self.n_users):
            user_ratings = rating_matrix[user_idx].toarray().flatten()
            rated_items = user_ratings.nonzero()[0]

            if len(rated_items) == 0:
                continue

            Y_rated = self.item_factors[rated_items]
            ratings = user_ratings[rated_items]

            A = YtY + regularization_diag + (self.regularization * len(rated_items)) * np.eye(self.factors)
            b = Y_rated.T.dot(ratings)

            self.user_factors[user_idx] = np.linalg.solve(A, b)

    def _update_item_factors(self, rating_matrix: csr_matrix) -> None:
        """Update item factors using least squares."""
        XtX = self.user_factors.T.dot(self.user_factors)
        regularization_diag = np.eye(self.factors) * self.regularization

        rating_matrix_t = rating_matrix.T.tocsr()

        for item_idx in range(self.n_items):
            item_ratings = rating_matrix_t[item_idx].toarray().flatten()
            rating_users = item_ratings.nonzero()[0]

            if len(rating_users) == 0:
                continue

            X_rated = self.user_factors[rating_users]
            ratings = item_ratings[rating_users]

            A = XtX + regularization_diag + (self.regularization * len(rating_users)) * np.eye(self.factors)
            b = X_rated.T.dot(ratings)

            self.item_factors[item_idx] = np.linalg.solve(A, b)

    def _calculate_rmse(self, rating_matrix: csr_matrix) -> float:
        """Calculate RMSE on training data."""
        predictions = []
        actuals = []

        for user_idx in range(min(100, self.n_users)):  # Sample for efficiency
            user_ratings = rating_matrix[user_idx].toarray().flatten()
            rated_items = user_ratings.nonzero()[0]

            for item_idx in rated_items:
                pred = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
                predictions.append(pred)
                actuals.append(user_ratings[item_idx])

        if len(predictions) == 0:
            return float('inf')

        return np.sqrt(mean_squared_error(actuals, predictions))

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
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        recommendations = []

        for user_id in user_ids:
            try:
                user_idx = self.user_encoder.transform([user_id])[0]
            except ValueError:
                # Unknown user - return empty recommendations
                continue

            # Calculate scores for all items
            user_vector = self.user_factors[user_idx]
            scores = np.dot(self.item_factors, user_vector)

            # Get top N items
            top_items = np.argsort(scores)[::-1][:n_recommendations]
            top_scores = scores[top_items]

            # Convert back to original item IDs
            item_ids = self.item_encoder.inverse_transform(top_items)

            for item_id, score in zip(item_ids, top_scores):
                recommendations.append({
                    'user_id': user_id,
                    'item_id': item_id,
                    'score': float(score)
                })

        return pd.DataFrame(recommendations)

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

        if isinstance(user_ids, str):
            user_ids = [user_ids]
        if isinstance(item_ids, str):
            item_ids = [item_ids]

        scores = []
        for user_id, item_id in zip(user_ids, item_ids):
            try:
                user_idx = self.user_encoder.transform([user_id])[0]
                item_idx = self.item_encoder.transform([item_id])[0]

                score = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
                scores.append(float(score))
            except ValueError:
                # Unknown user or item
                scores.append(self.global_mean if self.global_mean else 0.0)

        return np.array(scores)
