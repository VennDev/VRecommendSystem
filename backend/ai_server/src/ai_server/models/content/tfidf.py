"""
TF-IDF Content-Based Filtering Implementation
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import time

from ..base_model import BaseRecommender


class TFIDFRecommender(BaseRecommender):
    """
    Content-based recommender using TF-IDF vectorization.
    
    This model recommends items based on textual content similarity.
    It uses TF-IDF to vectorize item descriptions and cosine similarity
    to find similar items for recommendation.
    
    Parameters:
    -----------
    max_features : int, default=5000
        Maximum number of features for TF-IDF
    min_df : int, default=2
        Minimum document frequency for TF-IDF
    max_df : float, default=0.8
        Maximum document frequency for TF-IDF
    stop_words : str, default='english'
        Stop words to remove
    ngram_range : tuple, default=(1, 2)
        N-gram range for TF-IDF
    """

    def __init__(self, max_features: int = 5000, min_df: int = 2,
                 max_df: float = 0.8, stop_words: str = 'english',
                 ngram_range: tuple = (1, 2), **kwargs):
        super().__init__(max_features=max_features, min_df=min_df,
                         max_df=max_df, stop_words=stop_words,
                         ngram_range=ngram_range, **kwargs)

        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df
        self.stop_words = stop_words
        self.ngram_range = ngram_range

        self.tfidf_vectorizer = None
        self.item_features_matrix = None
        self.item_similarity_matrix = None
        self.user_profiles = None

    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'TFIDFRecommender':
        """
        Train the TF-IDF content-based model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id'] and optionally 'rating'
            user_features: Not used in TF-IDF model (for API consistency)
            item_features: DataFrame with columns ['item_id', 'content'] where content is text
            
        Returns:
            Self for method chaining
        """
        self._validate_input(interaction_data)

        if item_features is None:
            raise ValueError("TF-IDF model requires item_features with 'content' column")

        if 'content' not in item_features.columns:
            raise ValueError("item_features must have 'content' column with text data")

        print(f"Training TF-IDF model with {len(interaction_data)} interactions...")
        start_time = time.time()

        # Encode users and items
        data = self._encode_users_items(interaction_data.copy())

        # Prepare item content data
        item_content = item_features.copy()
        item_content = self._encode_items_for_content(item_content)

        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words=self.stop_words,
            ngram_range=self.ngram_range
        )

        # Fit TF-IDF on item content
        item_content_text = item_content['content'].fillna('').astype(str)
        self.item_features_matrix = self.tfidf_vectorizer.fit_transform(item_content_text)

        # Calculate item-item similarity matrix
        print("Computing item similarity matrix...")
        self.item_similarity_matrix = cosine_similarity(self.item_features_matrix)

        # Build user profiles based on interaction history
        print("Building user profiles...")
        self.user_profiles = self._build_user_profiles(data, item_content)

        training_time = time.time() - start_time
        self.metrics = {
            'training_time': training_time,
            'n_items': len(item_content),
            'n_features': self.item_features_matrix.shape[1],
            'vocab_size': len(self.tfidf_vectorizer.vocabulary_)
        }

        self.is_fitted = True
        print(f"Training completed in {training_time:.2f}s")

        return self

    def _encode_items_for_content(self, item_features: pd.DataFrame) -> pd.DataFrame:
        """Encode item IDs in the content features DataFrame."""
        # Create item encoder if not exists
        if self.item_encoder is None:
            from sklearn.preprocessing import LabelEncoder
            self.item_encoder = LabelEncoder()
            item_features['item_idx'] = self.item_encoder.fit_transform(item_features['item_id'])
        else:
            # Filter to only known items
            known_items = set(self.item_encoder.classes_)
            item_features = item_features[item_features['item_id'].isin(known_items)]
            item_features['item_idx'] = self.item_encoder.transform(item_features['item_id'])

        # Sort by item_idx to ensure proper alignment
        item_features = item_features.sort_values('item_idx').reset_index(drop=True)
        return item_features

    def _build_user_profiles(self, interaction_data: pd.DataFrame,
                             item_content: pd.DataFrame) -> dict:
        """Build user profiles based on TF-IDF vectors of interacted items."""
        user_profiles = {}

        # Create mapping from item_idx to row in content matrix
        item_idx_to_row = {item_content.iloc[i]['item_idx']: i
                           for i in range(len(item_content))}

        # Group interactions by user
        user_interactions = interaction_data.groupby('user_idx')['item_idx'].apply(list).to_dict()

        for user_idx, item_indices in user_interactions.items():
            # Get TF-IDF vectors for user's items
            user_item_vectors = []

            for item_idx in item_indices:
                if item_idx in item_idx_to_row:
                    row_idx = item_idx_to_row[item_idx]
                    user_item_vectors.append(self.item_features_matrix[row_idx])

            if user_item_vectors:
                # Average the TF-IDF vectors (weighted by rating if available)
                if 'rating' in interaction_data.columns:
                    user_ratings = interaction_data[
                        interaction_data['user_idx'] == user_idx
                        ]['rating'].values
                    weights = user_ratings / user_ratings.sum()

                    user_profile = csr_matrix((1, self.item_features_matrix.shape[1]))
                    for vector, weight in zip(user_item_vectors, weights):
                        user_profile += weight * vector
                else:
                    # Simple average
                    user_profile = sum(user_item_vectors) / len(user_item_vectors)

                user_profiles[user_idx] = user_profile

        return user_profiles

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

            if user_idx not in self.user_profiles:
                # User has no interaction history
                continue

            # Get user profile
            user_profile = self.user_profiles[user_idx]

            # Calculate similarity scores with all items
            if hasattr(user_profile, 'toarray'):
                user_profile = user_profile.toarray()

            scores = cosine_similarity(user_profile, self.item_features_matrix).flatten()

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

                if user_idx in self.user_profiles:
                    user_profile = self.user_profiles[user_idx]
                    if hasattr(user_profile, 'toarray'):
                        user_profile = user_profile.toarray()

                    item_vector = self.item_features_matrix[item_idx]
                    score = cosine_similarity(user_profile, item_vector)[0, 0]
                    scores.append(float(score))
                else:
                    scores.append(0.0)

            except ValueError:
                # Unknown user or item
                scores.append(0.0)

        return np.array(scores)

    def get_similar_items(self, item_id: str, n_similar: int = 10) -> pd.DataFrame:
        """
        Get items similar to a given item.
        
        Args:
            item_id: Item ID to find similar items for
            n_similar: Number of similar items to return
            
        Returns:
            DataFrame with columns ['item_id', 'similarity']
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before finding similar items")

        try:
            item_idx = self.item_encoder.transform([item_id])[0]
        except ValueError:
            return pd.DataFrame(columns=['item_id', 'similarity'])

        # Get similarity scores for this item
        similarities = self.item_similarity_matrix[item_idx]

        # Get top N similar items (excluding the item itself)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]
        similar_scores = similarities[similar_indices]

        # Convert back to original item IDs
        similar_item_ids = self.item_encoder.inverse_transform(similar_indices)

        similar_items = pd.DataFrame({
            'item_id': similar_item_ids,
            'similarity': similar_scores
        })

        return similar_items
