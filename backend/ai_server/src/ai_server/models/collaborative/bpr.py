"""
Bayesian Personalized Ranking (BPR) Implementation
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Tuple
import time
import random

from ..base_model import BaseRecommender


class BPRRecommender(BaseRecommender):
    """
    Bayesian Personalized Ranking for implicit feedback collaborative filtering.
    
    BPR optimizes for the ranking of items rather than rating prediction.
    It learns from implicit feedback by assuming users prefer items they
    interacted with over items they didn't interact with.
    
    Parameters:
    -----------
    factors : int, default=100
        Number of latent factors
    learning_rate : float, default=0.05
        Learning rate for SGD
    regularization : float, default=0.01
        Regularization parameter
    iterations : int, default=100
        Number of training iterations
    random_state : int, default=42
        Random seed for reproducibility
    """

    def __init__(self, factors: int = 100, learning_rate: float = 0.05,
                 regularization: float = 0.01, iterations: int = 100,
                 random_state: int = 42, **kwargs):
        super().__init__(factors=factors, learning_rate=learning_rate,
                         regularization=regularization, iterations=iterations,
                         random_state=random_state, **kwargs)

        self.user_items = None
        self.n_items = None
        self.n_users = None
        self.factors = factors
        self.learning_rate = learning_rate
        self.regularization = regularization
        self.iterations = iterations
        self.random_state = random_state

        self.user_factors = None
        self.item_factors = None
        self.item_bias = None

    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'BPRRecommender':
        """
        Train the BPR model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id'] and optionally 'rating'
            user_features: Not used in BPR (for API consistency)
            item_features: Not used in BPR (for API consistency)
            
        Returns:
            Self for method chaining
        """
        self._validate_input(interaction_data)

        print(f"Training BPR model with {len(interaction_data)} interactions...")
        start_time = time.time()

        # Encode users and items
        data = self._encode_users_items(interaction_data.copy())

        self.n_users = len(self.user_encoder.classes_)
        self.n_items = len(self.item_encoder.classes_)

        # Create user-item interaction matrix
        self.user_items = self._create_user_item_dict(data)

        # Initialize parameters
        np.random.seed(self.random_state)
        self.user_factors = np.random.normal(
            scale=1.0 / self.factors, size=(self.n_users, self.factors)
        )
        self.item_factors = np.random.normal(
            scale=1.0 / self.factors, size=(self.n_items, self.factors)
        )
        self.item_bias = np.zeros(self.n_items)

        # Training loop
        random.seed(self.random_state)

        for iteration in range(self.iterations):
            # Sample training triplets and update
            for _ in range(len(data)):
                self._update_factors()

            # Log progress
            if iteration % 20 == 0:
                print(f"Iteration {iteration}/{self.iterations}")
                self.training_history.append({'iteration': iteration})

        training_time = time.time() - start_time
        self.metrics = {
            'training_time': training_time,
            'iterations': self.iterations,
            'n_users': self.n_users,
            'n_items': self.n_items
        }

        self.is_fitted = True
        print(f"Training completed in {training_time:.2f}s")

        return self

    def _create_user_item_dict(self, data: pd.DataFrame) -> dict:
        """Create dictionary mapping users to their interacted items."""
        user_items = {}
        for _, row in data.iterrows():
            user_idx = row['user_idx']
            item_idx = row['item_idx']

            if user_idx not in user_items:
                user_items[user_idx] = set()
            user_items[user_idx].add(item_idx)

        return user_items

    def _sample_triplet(self) -> Tuple[int, int, int]:
        """Sample a (user, positive_item, negative_item) triplet."""
        # Sample user
        user_idx = random.choice(list(self.user_items.keys()))

        # Sample positive item
        positive_items = list(self.user_items[user_idx])
        positive_item = random.choice(positive_items)

        # Sample negative item
        negative_item = random.randint(0, self.n_items - 1)
        while negative_item in self.user_items[user_idx]:
            negative_item = random.randint(0, self.n_items - 1)

        return user_idx, positive_item, negative_item

    def _update_factors(self) -> None:
        """Perform one SGD update step."""
        user_idx, pos_item, neg_item = self._sample_triplet()

        # Calculate current scores
        pos_score = (np.dot(self.user_factors[user_idx], self.item_factors[pos_item]) +
                     self.item_bias[pos_item])
        neg_score = (np.dot(self.user_factors[user_idx], self.item_factors[neg_item]) +
                     self.item_bias[neg_item])

        # Calculate difference and sigmoid
        x_uij = pos_score - neg_score
        sigmoid = 1.0 / (1.0 + np.exp(x_uij))

        # Update factors
        user_factor = self.user_factors[user_idx]
        pos_item_factor = self.item_factors[pos_item]
        neg_item_factor = self.item_factors[neg_item]

        # User factor update
        self.user_factors[user_idx] += self.learning_rate * (
                sigmoid * (pos_item_factor - neg_item_factor) -
                self.regularization * user_factor
        )

        # Positive item factor update
        self.item_factors[pos_item] += self.learning_rate * (
                sigmoid * user_factor - self.regularization * pos_item_factor
        )

        # Negative item factor update
        self.item_factors[neg_item] += self.learning_rate * (
                -sigmoid * user_factor - self.regularization * neg_item_factor
        )

        # Bias updates
        self.item_bias[pos_item] += self.learning_rate * (
                sigmoid - self.regularization * self.item_bias[pos_item]
        )
        self.item_bias[neg_item] += self.learning_rate * (
                -sigmoid - self.regularization * self.item_bias[neg_item]
        )

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
            scores = np.dot(self.item_factors, user_vector) + self.item_bias

            # Remove items user has already interacted with
            if user_idx in self.user_items:
                for item_idx in self.user_items[user_idx]:
                    scores[item_idx] = -np.inf

            # Get top N items
            top_items = np.argsort(scores)[::-1][:n_recommendations]
            top_scores = scores[top_items]

            # Convert back to original item IDs
            item_ids = self.item_encoder.inverse_transform(top_items)

            for item_id, score in zip(item_ids, top_scores):
                if score != -np.inf:  # Skip filtered items
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

                score = (np.dot(self.user_factors[user_idx], self.item_factors[item_idx]) +
                         self.item_bias[item_idx])
                scores.append(float(score))
            except ValueError:
                # Unknown user or item
                scores.append(0.0)

        return np.array(scores)
