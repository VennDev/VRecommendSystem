from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd
import loguru
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity

from .base_model import BaseRecommendationModel, ModelRegistry


class SVDRecommendationModel(BaseRecommendationModel):
    """
    SVD-based recommendation model using TruncatedSVD
    Another fast, multithreaded alternative to LightFM
    """

    def __init__(self,
                 model_id: str = None,
                 n_components: int = 50,
                 algorithm: str = 'randomized',
                 n_iter: int = 5,
                 random_state: int = 42,
                 tol: float = 0.0,
                 **kwargs):

        super().__init__(
            model_id=model_id,
            n_components=n_components,
            algorithm=algorithm,
            n_iter=n_iter,
            random_state=random_state,
            tol=tol,
            **kwargs
        )

        self.model = TruncatedSVD(
            n_components=n_components,
            algorithm=algorithm,
            n_iter=n_iter,
            random_state=random_state,
            tol=tol
        )

        self.user_factors = None
        self.item_factors = None
        self.interaction_matrix = None
        self.global_mean = 0.0

    def fit(self,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            **kwargs) -> 'SVDRecommendationModel':

        start_time = datetime.now()

        # Data preprocessing (similar to NMF model)
        cleaned_interaction_data = self.validate_interaction_data(interaction_data)
        self.build_id_mappings(cleaned_interaction_data)
        self.calculate_training_stats(cleaned_interaction_data)

        # Calculate global mean
        if 'rating' in cleaned_interaction_data.columns:
            self.global_mean = cleaned_interaction_data['rating'].mean()

        # Build interaction matrix
        n_users = len(self.user_id_mapping)
        n_items = len(self.item_id_mapping)

        rows = []
        cols = []
        data = []

        for _, row in cleaned_interaction_data.iterrows():
            user_idx = self.user_id_mapping[row['user_id']]
            item_idx = self.item_id_mapping[row['item_id']]
            rating = row.get('rating', 1.0) - self.global_mean  # Center the data

            rows.append(user_idx)
            cols.append(item_idx)
            data.append(rating)

        self.interaction_matrix = sparse.csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items)
        )

        # Fit SVD model
        loguru.logger.info("Training SVD model...")
        self.user_factors = self.model.fit_transform(self.interaction_matrix)
        self.item_factors = self.model.components_.T

        training_time = (datetime.now() - start_time).total_seconds()

        explained_variance_ratio = self.model.explained_variance_ratio_.sum()

        self.metrics = {
            'training_time': training_time,
            'explained_variance_ratio': float(explained_variance_ratio),
            'n_users': len(self.user_id_mapping),
            'n_items': len(self.item_id_mapping),
            'n_interactions': len(cleaned_interaction_data),
            'sparsity': float(1 - (len(cleaned_interaction_data) / (n_users * n_items))),
            'n_components': self.hyperparameters['n_components']
        }

        self.is_fitted = True
        loguru.logger.info(f"SVD model trained in {training_time:.2f}s")

        return self

    def predict(self, user_ids: List[str], n_recommendations: int = 10, **kwargs) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        recommendations = []

        for user_id in user_ids:
            if user_id not in self.user_id_mapping:
                continue

            user_idx = self.user_id_mapping[user_id]
            user_vector = self.user_factors[user_idx]

            # Calculate scores for all items
            scores = np.dot(self.item_factors, user_vector) + self.global_mean

            # Get top recommendations
            top_items = np.argsort(scores)[::-1][:n_recommendations]

            for rank, item_idx in enumerate(top_items):
                if item_idx in self.reverse_item_mapping:
                    recommendations.append({
                        'user_id': user_id,
                        'item_id': self.reverse_item_mapping[item_idx],
                        'score': float(scores[item_idx]),
                        'rank': rank + 1
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

                user_vector = self.user_factors[user_idx]
                item_vector = self.item_factors[item_idx]

                score = np.dot(user_vector, item_vector) + self.global_mean
                scores.append(float(score))
            else:
                scores.append(self.global_mean)

        return scores

    def get_similar_items(self, item_id: str, n_similar: int = 10) -> List[Dict[str, Any]]:
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if item_id not in self.item_id_mapping:
            return []

        item_idx = self.item_id_mapping[item_id]
        item_vector = self.item_factors[item_idx].reshape(1, -1)

        similarities = cosine_similarity(item_vector, self.item_factors)[0]
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
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if user_id not in self.user_id_mapping:
            return []

        user_idx = self.user_id_mapping[user_id]
        user_vector = self.user_factors[user_idx].reshape(1, -1)

        similarities = cosine_similarity(user_vector, self.user_factors)[0]
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]

        similar_users = []
        for idx in similar_indices:
            if idx in self.reverse_user_mapping:
                similar_users.append({
                    'user_id': self.reverse_user_mapping[idx],
                    'similarity': float(similarities[idx])
                })

        return similar_users

    def _get_save_data(self) -> Dict[str, Any]:
        return {
            'user_factors': self.user_factors,
            'item_factors': self.item_factors,
            'interaction_matrix': self.interaction_matrix,
            'global_mean': self.global_mean
        }

    def _load_additional_data(self, model_data: Dict[str, Any]):
        self.user_factors = model_data.get('user_factors')
        self.item_factors = model_data.get('item_factors')
        self.interaction_matrix = model_data.get('interaction_matrix')
        self.global_mean = model_data.get('global_mean', 0.0)


ModelRegistry.register('svd', SVDRecommendationModel)
