"""
Feature-Based Content Filtering Implementation
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
import time

from ..base_model import BaseRecommender


class FeatureBasedRecommender(BaseRecommender):
    """
    Content-based recommender using multiple item features.
    
    This model uses numerical and categorical features of items to compute
    similarity and make recommendations. It can handle mixed data types
    and applies appropriate preprocessing to each feature type.
    
    Parameters:
    -----------
    categorical_features : list, default=None
        List of categorical feature column names
    numerical_features : list, default=None
        List of numerical feature column names
    feature_weights : dict, default=None
        Dictionary mapping feature names to their weights
    similarity_metric : str, default='cosine'
        Similarity metric to use ('cosine', 'euclidean')
    normalize_features : bool, default=True
        Whether to normalize numerical features
    """

    def __init__(self, categorical_features: Optional[List[str]] = None,
                 numerical_features: Optional[List[str]] = None,
                 feature_weights: Optional[Dict[str, float]] = None,
                 similarity_metric: str = 'cosine',
                 normalize_features: bool = True, **kwargs):
        super().__init__(categorical_features=categorical_features,
                         numerical_features=numerical_features,
                         feature_weights=feature_weights,
                         similarity_metric=similarity_metric,
                         normalize_features=normalize_features, **kwargs)

        self.categorical_features = categorical_features or []
        self.numerical_features = numerical_features or []
        self.feature_weights = feature_weights or {}
        self.similarity_metric = similarity_metric
        self.normalize_features = normalize_features

        self.feature_matrix: Optional[np.ndarray] = None
        self.item_similarity_matrix: Optional[np.ndarray] = None
        self.user_profiles: Optional[Dict[int, np.ndarray]] = None
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}

    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'FeatureBasedRecommender':
        """
        Train the feature-based content model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id'] and optionally 'rating'
            user_features: Not used in basic feature-based model (for API consistency)
            item_features: DataFrame with item features
            
        Returns:
            Self for method chaining
        """
        # Note: user_features parameter is kept for API consistency but not used
        _ = user_features  # Explicitly mark as unused to avoid linting warnings
        self._validate_input(interaction_data)

        if item_features is None:
            raise ValueError("Feature-based model requires item_features DataFrame")

        print(f"Training Feature-based model with {len(interaction_data)} interactions...")
        start_time = time.time()

        # Encode users and items
        data = self._encode_users_items(interaction_data.copy())

        # Prepare item features
        item_features_processed = self._process_item_features(item_features.copy())

        # Build feature matrix
        self.feature_matrix = self._build_feature_matrix(item_features_processed)

        # Calculate item similarity matrix
        print("Computing item similarity matrix...")
        self.item_similarity_matrix = self._compute_similarity_matrix()

        # Build user profiles
        print("Building user profiles...")
        self.user_profiles = self._build_user_profiles(data, item_features_processed)

        training_time = time.time() - start_time
        self.metrics = {
            'training_time': training_time,
            'n_items': len(item_features_processed),
            'n_features': self.feature_matrix.shape[1],
            'categorical_features': len(self.categorical_features),
            'numerical_features': len(self.numerical_features)
        }

        self.is_fitted = True
        print(f"Training completed in {training_time:.2f}s")

        return self

    def _process_item_features(self, item_features: pd.DataFrame) -> pd.DataFrame:
        """Process and encode item features."""
        # Auto-detect feature types if not specified
        if not self.categorical_features and not self.numerical_features:
            self._auto_detect_feature_types(item_features)

        # Encode item IDs
        item_features = self._encode_items_for_content(item_features)

        return item_features

    def _auto_detect_feature_types(self, item_features: pd.DataFrame) -> None:
        """Automatically detect categorical and numerical features."""
        exclude_cols = ['item_id', 'item_idx']

        for col in item_features.columns:
            if col in exclude_cols:
                continue

            if item_features[col].dtype in ['object', 'category']:
                self.categorical_features.append(col)
            elif item_features[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                self.numerical_features.append(col)

    def _encode_items_for_content(self, item_features: pd.DataFrame) -> pd.DataFrame:
        """Encode item IDs in the content features DataFrame."""
        # Create item encoder if not exists
        if self.item_encoder is None:
            from sklearn.preprocessing import LabelEncoder
            self.item_encoder = LabelEncoder()
            item_features['item_idx'] = self.item_encoder.fit_transform(item_features['item_id'])
        else:
            # Filter to only known items
            known_items_array = self.item_encoder.classes_
            if known_items_array is not None:
                known_items = list(known_items_array)
                filtered_mask = item_features['item_id'].isin(known_items)
                item_features_filtered = item_features[filtered_mask].copy()
                if isinstance(item_features_filtered, pd.DataFrame):
                    item_features = item_features_filtered
                    item_features['item_idx'] = self.item_encoder.transform(item_features['item_id'])

        # Sort by item_idx to ensure proper alignment
        item_features = item_features.sort_values('item_idx').reset_index(drop=True)
        return item_features

    def _build_feature_matrix(self, item_features: pd.DataFrame) -> np.ndarray:
        """Build the feature matrix from processed item features."""
        feature_vectors = []

        # Process categorical features
        for feature in self.categorical_features:
            if feature not in item_features.columns:
                continue

            # One-hot encode categorical features
            if feature not in self.encoders:
                encoder = LabelEncoder()
                encoded_values = encoder.fit_transform(item_features[feature].fillna('unknown'))
                self.encoders[feature] = encoder
            else:
                encoded_values = self.encoders[feature].transform(item_features[feature].fillna('unknown'))

            # Convert to one-hot
            encoder_classes = self.encoders[feature].classes_
            if encoder_classes is not None:
                n_categories = len(encoder_classes)
                one_hot = np.eye(n_categories)[encoded_values]
                feature_vectors.append(one_hot)

        # Process numerical features
        for feature in self.numerical_features:
            if feature not in item_features.columns:
                continue

            values = item_features[feature].fillna(0).values
            # Ensure values is numpy array and reshape properly
            values = np.array(values).reshape(-1, 1)

            if self.normalize_features:
                if feature not in self.scalers:
                    scaler = StandardScaler()
                    scaled_values = scaler.fit_transform(values)
                    self.scalers[feature] = scaler
                else:
                    scaled_values = self.scalers[feature].transform(values)

                feature_vectors.append(scaled_values)
            else:
                feature_vectors.append(values)

        # Combine all features
        if feature_vectors:
            feature_matrix = np.concatenate(feature_vectors, axis=1)
        else:
            raise ValueError("No valid features found in item_features")

        # Apply feature weights if specified
        if self.feature_weights:
            weighted_matrix = self._apply_feature_weights(feature_matrix)
            return weighted_matrix

        return feature_matrix

    def _apply_feature_weights(self, feature_matrix: np.ndarray) -> np.ndarray:
        """Apply feature weights to the feature matrix."""
        # This is a simplified implementation
        # In practice, you'd want to track which columns correspond to which features
        # Note: item_features parameter removed as it's not used in this simple implementation
        return feature_matrix

    def _compute_similarity_matrix(self) -> np.ndarray:
        """Compute item-item similarity matrix."""
        if self.feature_matrix is None:
            raise ValueError("Feature matrix not built yet")
            
        if self.similarity_metric == 'cosine':
            return cosine_similarity(self.feature_matrix)
        elif self.similarity_metric == 'euclidean':
            from sklearn.metrics.pairwise import euclidean_distances
            distances = euclidean_distances(self.feature_matrix)
            # Convert distances to similarities
            return 1 / (1 + distances)
        else:
            raise ValueError(f"Unsupported similarity metric: {self.similarity_metric}")

    def _build_user_profiles(self, interaction_data: pd.DataFrame,
                             item_features: pd.DataFrame) -> Dict[int, np.ndarray]:
        """Build user profiles based on item features."""
        if self.feature_matrix is None:
            raise ValueError("Feature matrix not built yet")
            
        user_profiles = {}

        # Create mapping from item_idx to row in feature matrix
        item_idx_to_row = {int(item_features.iloc[i]['item_idx']): i
                           for i in range(len(item_features))}

        # Group interactions by user
        user_interactions_series = interaction_data.groupby('user_idx')['item_idx'].apply(list)
        user_interactions = user_interactions_series.to_dict()

        for user_idx, item_indices in user_interactions.items():
            # Get feature vectors for user's items
            user_item_features = []

            for item_idx in item_indices:
                if item_idx in item_idx_to_row:
                    row_idx = item_idx_to_row[item_idx]
                    user_item_features.append(self.feature_matrix[row_idx])

            if user_item_features:
                # Average the feature vectors (weighted by rating if available)
                if 'rating' in interaction_data.columns:
                    user_data = interaction_data[interaction_data['user_idx'] == user_idx]
                    rating_series = user_data['rating']
                    # Convert pandas Series to numpy array
                    user_ratings = np.array(rating_series)
                    user_ratings_sum = float(np.sum(user_ratings))
                    
                    if user_ratings_sum > 0:
                        weights = user_ratings / user_ratings_sum
                        user_profile = np.zeros(self.feature_matrix.shape[1])
                        for features, weight in zip(user_item_features, weights):
                            user_profile += weight * features
                    else:
                        user_profile = np.mean(user_item_features, axis=0)
                else:
                    # Simple average
                    user_profile = np.mean(user_item_features, axis=0)

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
        if not self.is_fitted or self.feature_matrix is None or self.user_profiles is None:
            raise ValueError("Model must be fitted before making predictions")

        if isinstance(user_ids, str):
            user_ids = [user_ids]

        recommendations = []

        for user_id in user_ids:
            if self.user_encoder is None:
                continue
                
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
            scores: np.ndarray
            if self.similarity_metric == 'cosine':
                scores = cosine_similarity([user_profile], self.feature_matrix).flatten()
            elif self.similarity_metric == 'euclidean':
                from sklearn.metrics.pairwise import euclidean_distances
                distances = euclidean_distances([user_profile], self.feature_matrix).flatten()
                scores = 1 / (1 + distances)
            else:
                continue

            # Get top N items
            top_items = np.argsort(scores)[::-1][:n_recommendations]
            top_scores = scores[top_items]

            # Convert back to original item IDs
            if self.item_encoder is not None:
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
        if not self.is_fitted or self.feature_matrix is None or self.user_profiles is None:
            raise ValueError("Model must be fitted before making predictions")

        if isinstance(user_ids, str):
            user_ids = [user_ids]
        if isinstance(item_ids, str):
            item_ids = [item_ids]

        scores = []

        for user_id, item_id in zip(user_ids, item_ids):
            if self.user_encoder is None or self.item_encoder is None:
                scores.append(0.0)
                continue
                
            try:
                user_idx = self.user_encoder.transform([user_id])[0]
                item_idx = self.item_encoder.transform([item_id])[0]

                if user_idx in self.user_profiles:
                    user_profile = self.user_profiles[user_idx]
                    item_features = self.feature_matrix[item_idx]

                    score: float
                    if self.similarity_metric == 'cosine':
                        score = cosine_similarity([user_profile], [item_features])[0, 0]
                    elif self.similarity_metric == 'euclidean':
                        from sklearn.metrics.pairwise import euclidean_distances
                        distance = euclidean_distances([user_profile], [item_features])[0, 0]
                        score = 1 / (1 + distance)
                    else:
                        score = 0.0

                    scores.append(float(score))
                else:
                    scores.append(0.0)

            except ValueError:
                # Unknown user or item
                scores.append(0.0)

        return np.array(scores)
