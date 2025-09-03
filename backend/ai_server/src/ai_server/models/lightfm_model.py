import os
import pickle
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd
import loguru

from .base_model import BaseRecommendationModel, ModelRegistry

try:
    from lightfm import LightFM
    from lightfm.data import Dataset
    from lightfm.evaluation import precision_at_k, recall_at_k, auc_score
    from lightfm.cross_validation import random_train_test_split

    HAS_LIGHTFM = True
except ImportError:
    HAS_LIGHTFM = False


class LightFMModel(BaseRecommendationModel):
    """
    Recommender using LightFM library
    Supports both collaborative and content-based filtering in one model
    """

    def __init__(self,
                 model_id: str = None,
                 loss: str = 'warp',  # 'logistic', 'bpr', 'warp', 'warp-kos'
                 learning_rate: float = 0.05,
                 item_alpha: float = 0.0,
                 user_alpha: float = 0.0,
                 no_components: int = 10,
                 max_sampled: int = 10,
                 random_state: int = 42,
                 **kwargs):

        if not HAS_LIGHTFM:
            raise ImportError("LightFM is required: pip install lightfm")

        # Initialize base class
        super().__init__(
            model_id=model_id,
            loss=loss,
            learning_rate=learning_rate,
            item_alpha=item_alpha,
            user_alpha=user_alpha,
            no_components=no_components,
            max_sampled=max_sampled,
            random_state=random_state,
            **kwargs
        )

        # LightFM specific attributes
        self.model = LightFM(**self.hyperparameters)
        self.dataset = Dataset()
        self.interaction_matrix = None
        self.user_features_matrix = None
        self.item_features_matrix = None

    def fit(self,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            epochs: int = 10) -> 'LightFMModel':

        start_time = datetime.now()

        # Validate and clean data using base class methods
        cleaned_interaction_data = self.validate_interaction_data(interaction_data)

        if user_features is not None:
            user_features = self.validate_feature_data(user_features, 'user')

        if item_features is not None:
            item_features = self.validate_feature_data(item_features, 'item')

        # Build ID mappings using base class method
        self.build_id_mappings(cleaned_interaction_data)

        # Calculate training statistics using base class method
        self.calculate_training_stats(cleaned_interaction_data)

        # Build dataset
        users = cleaned_interaction_data['user_id'].unique()
        items = cleaned_interaction_data['item_id'].unique()

        # Prepare user features
        user_feature_names = []
        if user_features is not None:
            # Auto-detect features (exclude id columns)
            feature_cols = [col for col in user_features.columns if col != 'user_id']
            user_feature_names = [f"user_{col}_{val}"
                                  for col in feature_cols
                                  for val in user_features[col].unique()]

        # Prepare item features
        item_feature_names = []
        if item_features is not None:
            feature_cols = [col for col in item_features.columns if col != 'item_id']
            item_feature_names = [f"item_{col}_{val}"
                                  for col in feature_cols
                                  for val in item_features[col].unique()]

        # Fit dataset
        self.dataset.fit(
            users=users,
            items=items,
            user_features=user_feature_names,
            item_features=item_feature_names
        )

        # Build interaction matrix
        weights = interaction_data['rating'].values if 'rating' in interaction_data.columns else None
        interactions, _ = self.dataset.build_interactions(
            [(row['user_id'], row['item_id'], weights[i] if weights is not None else 1.0)
             for i, (_, row) in enumerate(interaction_data.iterrows())]
        )

        self.interaction_matrix = interactions

        # Build user features matrix
        if user_features is not None:
            user_feature_list = []
            for _, user_row in user_features.iterrows():
                user_id = user_row['user_id']
                features = []
                for col in [c for c in user_features.columns if c != 'user_id']:
                    features.append(f"user_{col}_{user_row[col]}")
                user_feature_list.append((user_id, features))

            self.user_features_matrix, _ = self.dataset.build_user_features(user_feature_list)

        # Build item features matrix
        if item_features is not None:
            item_feature_list = []
            for _, item_row in item_features.iterrows():
                item_id = item_row['item_id']
                features = []
                for col in [c for c in item_features.columns if c != 'item_id']:
                    if col == 'content':  # Handle text content
                        # Simple text processing - split words
                        words = str(item_row[col]).lower().split()[:50]  # Limit words
                        features.extend([f"word_{word}" for word in words])
                    else:
                        features.append(f"item_{col}_{item_row[col]}")
                item_feature_list.append((item_id, features))

            # Add text features to dataset if needed
            if 'content' in item_features.columns:
                all_words = set()
                for _, row in item_features.iterrows():
                    words = str(row['content']).lower().split()[:50]
                    all_words.update([f"word_{word}" for word in words])

                # Refit with text features
                self.dataset.fit(
                    users=users,
                    items=items,
                    user_features=user_feature_names,
                    item_features=item_feature_names + list(all_words)
                )

                # Rebuild matrices
                interactions, _ = self.dataset.build_interactions(
                    [(row['user_id'], row['item_id'], weights[i] if weights is not None else 1.0)
                     for i, (_, row) in enumerate(interaction_data.iterrows())]
                )
                self.interaction_matrix = interactions

                if user_features is not None:
                    self.user_features_matrix, _ = self.dataset.build_user_features(user_feature_list)

            self.item_features_matrix, _ = self.dataset.build_item_features(item_feature_list)

        # Train model
        self.model.fit(
            self.interaction_matrix,
            user_features=self.user_features_matrix,
            item_features=self.item_features_matrix,
            epochs=epochs,
            verbose=True
        )

        # Store mappings
        self.user_id_mapping = self.dataset.mapping()[0]
        self.item_id_mapping = self.dataset.mapping()[2]

        # Calculate metrics
        training_time = (datetime.now() - start_time).total_seconds()
        self.metrics = {
            'training_time': training_time,
            'n_users': len(users),
            'n_items': len(items),
            'n_interactions': len(interaction_data),
            'sparsity': 1 - (len(interaction_data) / (len(users) * len(items))),
            'has_user_features': user_features is not None,
            'has_item_features': item_features is not None
        }

        self.is_fitted = True
        loguru.logger.info(f"Model trained in {training_time:.2f}s")
        return self

    def predict(self, user_ids: List[str], n_recommendations: int = 10, **kwargs) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        recommendations = []

        for user_id in user_ids:
            if user_id not in self.user_id_mapping:
                continue

            user_idx = self.user_id_mapping[user_id]

            # Get all item scores
            scores = self.model.predict(
                user_idx,
                np.arange(len(self.item_id_mapping)),
                user_features=self.user_features_matrix,
                item_features=self.item_features_matrix
            )

            # Get top recommendations
            top_items_idx = np.argsort(scores)[::-1][:n_recommendations]

            # Convert back to item_ids
            reverse_item_mapping = {v: k for k, v in self.item_id_mapping.items()}

            for item_idx in top_items_idx:
                if item_idx in reverse_item_mapping:
                    recommendations.append({
                        'user_id': user_id,
                        'item_id': reverse_item_mapping[item_idx],
                        'score': float(scores[item_idx])
                    })

        return pd.DataFrame(recommendations)

    def predict_score(self, user_ids: List[str], item_ids: List[str]) -> List[float]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        scores = []
        for user_id, item_id in zip(user_ids, item_ids):
            if user_id in self.user_id_mapping and item_id in self.item_id_mapping:
                user_idx = self.user_id_mapping[user_id]
                item_idx = self.item_id_mapping[item_id]

                score = self.model.predict(
                    user_idx,
                    [item_idx],
                    user_features=self.user_features_matrix,
                    item_features=self.item_features_matrix
                )[0]
                scores.append(float(score))
            else:
                scores.append(0.0)

        return scores

    def evaluate(self, test_data: pd.DataFrame, k_values: List[int] = [5, 10, 20], **kwargs) -> Dict[str, float]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Build test interactions
        test_interactions, _ = self.dataset.build_interactions(
            [(row['user_id'], row['item_id'], 1.0)
             for _, row in test_data.iterrows()]
        )

        metrics = {}
        for k in k_values:
            precision = precision_at_k(
                self.model,
                test_interactions,
                train_interactions=self.interaction_matrix,
                k=k,
                user_features=self.user_features_matrix,
                item_features=self.item_features_matrix
            ).mean()

            recall = recall_at_k(
                self.model,
                test_interactions,
                train_interactions=self.interaction_matrix,
                k=k,
                user_features=self.user_features_matrix,
                item_features=self.item_features_matrix
            ).mean()

            metrics[f'precision@{k}'] = float(precision)
            metrics[f'recall@{k}'] = float(recall)

        return metrics

    def _get_save_data(self) -> Dict[str, Any]:
        """Get LightFM-specific data to save"""
        return {
            'dataset': self.dataset,
            'interaction_matrix': self.interaction_matrix,
            'user_features_matrix': self.user_features_matrix,
            'item_features_matrix': self.item_features_matrix
        }

    def _load_additional_data(self, model_data: Dict[str, Any]):
        """Load LightFM-specific data"""
        self.dataset = model_data.get('dataset')
        self.interaction_matrix = model_data.get('interaction_matrix')
        self.user_features_matrix = model_data.get('user_features_matrix')
        self.item_features_matrix = model_data.get('item_features_matrix')

    def get_similar_items(self, item_id: str, n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Get items similar to a given item based on LightFM embeddings.
        
        Args:
            item_id: Item ID to find similar items for
            n_similar: Number of similar items to return
            
        Returns:
            List of similar item dictionaries
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if item_id not in self.item_id_mapping:
            return []

        item_idx = self.item_id_mapping[item_id]

        # Get item embeddings
        item_embeddings = self.model.item_embeddings
        target_embedding = item_embeddings[item_idx]

        # Calculate similarities (cosine similarity)
        similarities = np.dot(item_embeddings, target_embedding) / (
                np.linalg.norm(item_embeddings, axis=1) * np.linalg.norm(target_embedding)
        )

        # Get top similar items (excluding the item itself)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]

        similar_items = []
        for idx in similar_indices:
            if idx in self.reverse_item_mapping:
                similar_items.append({
                    'item_id': self.reverse_item_mapping[idx],
                    'similarity': float(similarities[idx])
                })

        return similar_items

    def get_similar_users(self, user_id: str, n_similar: int = 10) -> List[Dict[str, Any]]:
        """
        Get users similar to a given user based on LightFM embeddings.
        
        Args:
            user_id: User ID to find similar users for
            n_similar: Number of similar users to return
            
        Returns:
            List of similar user dictionaries
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if user_id not in self.user_id_mapping:
            return []

        user_idx = self.user_id_mapping[user_id]

        # Get user embeddings
        user_embeddings = self.model.user_embeddings
        target_embedding = user_embeddings[user_idx]

        # Calculate similarities (cosine similarity)
        similarities = np.dot(user_embeddings, target_embedding) / (
                np.linalg.norm(user_embeddings, axis=1) * np.linalg.norm(target_embedding)
        )

        # Get top similar users (excluding the user itself)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]

        similar_users = []
        for idx in similar_indices:
            if idx in self.reverse_user_mapping:
                similar_users.append({
                    'user_id': self.reverse_user_mapping[idx],
                    'similarity': float(similarities[idx])
                })

        return similar_users


# Register the LightFM model in the registry
ModelRegistry.register('lightfm', LightFMModel)
