from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import loguru
from scipy import sparse
from sklearn.decomposition import NMF
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from . import ModelRegistry
from .base_model import BaseRecommendationModel


class NMFRecommendationModel(BaseRecommendationModel):
    """
    Matrix Factorization using Non-negative Matrix Factorization (NMF)
    Fast, multithreaded alternative to LightFM with similar functionality
    """

    def __init__(self,
                 model_id: str = None,
                 n_components: int = 50,
                 init: str = 'random',
                 solver: str = 'mu',  # 'mu' or 'cd'
                 beta_loss: str = 'frobenius',
                 tol: float = 1e-4,
                 max_iter: int = 200,
                 random_state: int = 42,
                 alpha: float = 0.0,
                 l1_ratio: float = 0.0,
                 **kwargs):

        super().__init__(
            model_id=model_id,
            n_components=n_components,
            init=init,
            solver=solver,
            beta_loss=beta_loss,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
            alpha=alpha,
            l1_ratio=l1_ratio,
            **kwargs
        )

        # Initialize NMF model
        self.model = NMF(
            n_components=n_components,
            init=init,
            solver=solver,
            beta_loss=beta_loss,
            tol=tol,
            max_iter=max_iter,
            random_state=random_state,
            alpha_W=alpha,
            alpha_H=alpha,
            l1_ratio=l1_ratio
        )

        # Model components
        self.user_factors = None
        self.item_factors = None
        self.interaction_matrix = None

        # Feature processing
        self.user_features_processor = None
        self.item_features_processor = None
        self.text_vectorizer = None

        # Feature matrices
        self.processed_user_features = None
        self.processed_item_features = None

        # Global statistics
        self.global_mean = 0.0
        self.user_bias = {}
        self.item_bias = {}

    def _preprocess_features(self,
                             user_features: Optional[pd.DataFrame] = None,
                             item_features: Optional[pd.DataFrame] = None) -> Tuple[
        Optional[np.ndarray], Optional[np.ndarray]]:
        """Preprocess user and item features"""

        processed_user_features = None
        processed_item_features = None

        # Process user features
        if user_features is not None:
            feature_cols = [col for col in user_features.columns if col != 'user_id']

            if feature_cols:
                # Separate numerical and categorical features
                numerical_cols = []
                categorical_cols = []

                for col in feature_cols:
                    if user_features[col].dtype in ['int64', 'float64']:
                        numerical_cols.append(col)
                    else:
                        categorical_cols.append(col)

                features_list = []

                # Process numerical features
                if numerical_cols:
                    numerical_data = user_features[numerical_cols].fillna(0)
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(numerical_data)
                    features_list.append(scaled_data)

                # Process categorical features (one-hot encoding)
                if categorical_cols:
                    categorical_features = []
                    for col in categorical_cols:
                        dummies = pd.get_dummies(user_features[col], prefix=col)
                        categorical_features.append(dummies.values)

                    if categorical_features:
                        categorical_data = np.hstack(categorical_features)
                        features_list.append(categorical_data)

                if features_list:
                    processed_user_features = np.hstack(features_list)

        # Process item features
        if item_features is not None:
            feature_cols = [col for col in item_features.columns if col != 'item_id']

            if feature_cols:
                features_list = []

                for col in feature_cols:
                    if col == 'content' or 'text' in col.lower():
                        # Text features
                        if self.text_vectorizer is None:
                            self.text_vectorizer = TfidfVectorizer(
                                max_features=1000,
                                stop_words='english',
                                ngram_range=(1, 2),
                                min_df=2
                            )

                        text_data = item_features[col].fillna('').astype(str)
                        text_features = self.text_vectorizer.fit_transform(text_data)
                        features_list.append(text_features.toarray())

                    elif item_features[col].dtype in ['int64', 'float64']:
                        # Numerical features
                        numerical_data = item_features[[col]].fillna(0)
                        scaler = StandardScaler()
                        scaled_data = scaler.fit_transform(numerical_data)
                        features_list.append(scaled_data)

                    else:
                        # Categorical features
                        dummies = pd.get_dummies(item_features[col], prefix=col)
                        features_list.append(dummies.values)

                if features_list:
                    processed_item_features = np.hstack(features_list)

        return processed_user_features, processed_item_features

    def _build_interaction_matrix(self, interaction_data: pd.DataFrame) -> sparse.csr_matrix:
        """Build user-item interaction matrix"""

        n_users = len(self.user_id_mapping)
        n_items = len(self.item_id_mapping)

        # Create arrays for sparse matrix
        rows = []
        cols = []
        data = []

        for _, row in interaction_data.iterrows():
            user_idx = self.user_id_mapping[row['user_id']]
            item_idx = self.item_id_mapping[row['item_id']]
            rating = row.get('rating', 1.0)

            rows.append(user_idx)
            cols.append(item_idx)
            data.append(rating)

        # Create sparse matrix
        interaction_matrix = sparse.csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_items)
        )

        return interaction_matrix

    def _calculate_bias_terms(self, interaction_data: pd.DataFrame):
        """Calculate global mean and bias terms"""

        if 'rating' in interaction_data.columns:
            self.global_mean = interaction_data['rating'].mean()

            # User bias
            user_ratings = interaction_data.groupby('user_id')['rating'].mean()
            for user_id, mean_rating in user_ratings.items():
                self.user_bias[user_id] = mean_rating - self.global_mean

            # Item bias
            item_ratings = interaction_data.groupby('item_id')['rating'].mean()
            for item_id, mean_rating in item_ratings.items():
                self.item_bias[item_id] = mean_rating - self.global_mean
        else:
            self.global_mean = 1.0

    def fit(self,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            **kwargs) -> 'NMFRecommendationModel':

        start_time = datetime.now()

        # Validate and clean data
        cleaned_interaction_data = self.validate_interaction_data(interaction_data)

        if user_features is not None:
            user_features = self.validate_feature_data(user_features, 'user')

        if item_features is not None:
            item_features = self.validate_feature_data(item_features, 'item')

        # Build ID mappings
        self.build_id_mappings(cleaned_interaction_data)

        # Calculate training statistics
        self.calculate_training_stats(cleaned_interaction_data)

        # Calculate bias terms
        self._calculate_bias_terms(cleaned_interaction_data)

        # Build interaction matrix
        self.interaction_matrix = self._build_interaction_matrix(cleaned_interaction_data)

        # Preprocess features
        self.processed_user_features, self.processed_item_features = self._preprocess_features(
            user_features, item_features
        )

        # Fit NMF model
        loguru.logger.info("Training NMF model...")
        self.user_factors = self.model.fit_transform(self.interaction_matrix)
        self.item_factors = self.model.components_.T

        # Incorporate features if available
        if self.processed_user_features is not None:
            # Combine collaborative and content-based features for users
            feature_weight = 0.3
            combined_user_features = (1 - feature_weight) * self.user_factors + \
                                     feature_weight * self.processed_user_features[:len(self.user_factors)]
            self.user_factors = combined_user_features

        if self.processed_item_features is not None:
            # Combine collaborative and content-based features for items
            feature_weight = 0.3
            combined_item_features = (1 - feature_weight) * self.item_factors + \
                                     feature_weight * self.processed_item_features[:len(self.item_factors)]
            self.item_factors = combined_item_features

        # Calculate training metrics
        training_time = (datetime.now() - start_time).total_seconds()

        reconstruction_error = self.model.reconstruction_err_

        self.metrics = {
            'training_time': training_time,
            'reconstruction_error': float(reconstruction_error),
            'n_users': len(self.user_id_mapping),
            'n_items': len(self.item_id_mapping),
            'n_interactions': len(cleaned_interaction_data),
            'sparsity': float(
                1 - (len(cleaned_interaction_data) / (len(self.user_id_mapping) * len(self.item_id_mapping)))),
            'has_user_features': user_features is not None,
            'has_item_features': item_features is not None,
            'n_components': self.hyperparameters['n_components']
        }

        self.is_fitted = True
        loguru.logger.info(
            f"NMF model trained in {training_time:.2f}s with reconstruction error: {reconstruction_error:.4f}")

        return self

    def predict(self, user_ids: List[str], n_recommendations: int = 10, **kwargs) -> pd.DataFrame:
        """Generate recommendations for users"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        recommendations = []

        for user_id in user_ids:
            if user_id not in self.user_id_mapping:
                loguru.logger.warning(f"User {user_id} not found in training data")
                continue

            user_idx = self.user_id_mapping[user_id]

            # Calculate scores for all items
            user_vector = self.user_factors[user_idx]
            scores = np.dot(self.item_factors, user_vector)

            # Add bias terms
            user_bias_val = self.user_bias.get(user_id, 0.0)
            for item_idx, item_id in self.reverse_item_mapping.items():
                item_bias_val = self.item_bias.get(item_id, 0.0)
                scores[item_idx] = scores[item_idx] + self.global_mean + user_bias_val + item_bias_val

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
        """Predict scores for specific user-item pairs"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        scores = []

        for user_id, item_id in zip(user_ids, item_ids):
            if user_id in self.user_id_mapping and item_id in self.item_id_mapping:
                user_idx = self.user_id_mapping[user_id]
                item_idx = self.item_id_mapping[item_id]

                # Calculate prediction
                user_vector = self.user_factors[user_idx]
                item_vector = self.item_factors[item_idx]

                score = np.dot(user_vector, item_vector)

                # Add bias terms
                user_bias_val = self.user_bias.get(user_id, 0.0)
                item_bias_val = self.item_bias.get(item_id, 0.0)

                final_score = score + self.global_mean + user_bias_val + item_bias_val
                scores.append(float(final_score))
            else:
                scores.append(self.global_mean)

        return scores

    def get_similar_items(self, item_id: str, n_similar: int = 10) -> List[Dict[str, Any]]:
        """Get items similar to a given item"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if item_id not in self.item_id_mapping:
            return []

        item_idx = self.item_id_mapping[item_id]
        item_vector = self.item_factors[item_idx].reshape(1, -1)

        # Calculate cosine similarities
        similarities = cosine_similarity(item_vector, self.item_factors)[0]

        # Get top similar items (excluding the item itself)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]

        similar_items = []
        for idx in similar_indices:
            if idx in self.reverse_item_mapping:
                similar_items.append({
                    'item_id': self.reverse_item_mapping[idx],
                    'similarity': float(similarities[idx]),
                    'rank': len(similar_items) + 1
                })

        return similar_items

    def get_similar_users(self, user_id: str, n_similar: int = 10) -> List[Dict[str, Any]]:
        """Get users similar to a given user"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        if user_id not in self.user_id_mapping:
            return []

        user_idx = self.user_id_mapping[user_id]
        user_vector = self.user_factors[user_idx].reshape(1, -1)

        # Calculate cosine similarities
        similarities = cosine_similarity(user_vector, self.user_factors)[0]

        # Get top similar users (excluding the user itself)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar + 1]

        similar_users = []
        for idx in similar_indices:
            if idx in self.reverse_user_mapping:
                similar_users.append({
                    'user_id': self.reverse_user_mapping[idx],
                    'similarity': float(similarities[idx]),
                    'rank': len(similar_users) + 1
                })

        return similar_users

    def evaluate(self,
                 test_data: pd.DataFrame,
                 k_values: List[int] = [5, 10, 20],
                 **kwargs) -> Dict[str, float]:
        """Evaluate the model on test data"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        # Prepare test data
        test_data_clean = self.validate_interaction_data(test_data)

        metrics = {}

        # Calculate metrics for each k value
        for k in k_values:
            precision_scores = []
            recall_scores = []

            # Group by user
            user_groups = test_data_clean.groupby('user_id')

            for user_id, user_interactions in user_groups:
                if user_id not in self.user_id_mapping:
                    continue

                # Get recommendations
                recommendations = self.predict([user_id], k)

                if recommendations.empty:
                    continue

                # Get ground truth items
                true_items = set(user_interactions['item_id'].values)
                recommended_items = set(recommendations['item_id'].values)

                # Calculate precision and recall
                if len(recommended_items) > 0:
                    intersection = len(true_items.intersection(recommended_items))
                    precision = intersection / len(recommended_items)
                    recall = intersection / len(true_items) if len(true_items) > 0 else 0.0

                    precision_scores.append(precision)
                    recall_scores.append(recall)

            # Average metrics
            if precision_scores:
                metrics[f'precision@{k}'] = float(np.mean(precision_scores))
                metrics[f'recall@{k}'] = float(np.mean(recall_scores))
            else:
                metrics[f'precision@{k}'] = 0.0
                metrics[f'recall@{k}'] = 0.0

        return metrics

    def _get_save_data(self) -> Dict[str, Any]:
        """Get model-specific data to save"""
        return {
            'user_factors': self.user_factors,
            'item_factors': self.item_factors,
            'interaction_matrix': self.interaction_matrix,
            'processed_user_features': self.processed_user_features,
            'processed_item_features': self.processed_item_features,
            'text_vectorizer': self.text_vectorizer,
            'global_mean': self.global_mean,
            'user_bias': self.user_bias,
            'item_bias': self.item_bias
        }

    def _load_additional_data(self, model_data: Dict[str, Any]):
        """Load model-specific data"""
        self.user_factors = model_data.get('user_factors')
        self.item_factors = model_data.get('item_factors')
        self.interaction_matrix = model_data.get('interaction_matrix')
        self.processed_user_features = model_data.get('processed_user_features')
        self.processed_item_features = model_data.get('processed_item_features')
        self.text_vectorizer = model_data.get('text_vectorizer')
        self.global_mean = model_data.get('global_mean', 0.0)
        self.user_bias = model_data.get('user_bias', {})
        self.item_bias = model_data.get('item_bias', {})


ModelRegistry.register("nmf", NMFRecommendationModel)
