"""
Evaluation metrics and utilities for recommendation systems.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Protocol
from sklearn.metrics import mean_squared_error, mean_absolute_error
import time


class RecommenderProtocol(Protocol):
    """Protocol for recommender models."""

    def fit(self, *args: Any, **kwargs: Any) -> Any: ...

    def predict(self, *args: Any, **kwargs: Any) -> pd.DataFrame: ...

    def get_hyperparameters(self) -> Dict[str, Any]: ...


class RecommenderEvaluator:
    """
    Evaluation utilities for recommendation systems.
    
    Provides metrics for both rating prediction and ranking tasks.
    """

    @staticmethod
    def evaluate_recommendations(predictions: pd.DataFrame,
                                 ground_truth: pd.DataFrame,
                                 k_values=None) -> Dict[str, float]:
        """
        Evaluate recommendation quality using ranking metrics.
        
        Args:
            predictions: DataFrame with columns ['user_id', 'item_id', 'score']
            ground_truth: DataFrame with columns ['user_id', 'item_id'] (and optionally 'rating')
            k_values: List of k values for evaluation
            
        Returns:
            Dictionary with evaluation metrics
        """
        if k_values is None:
            k_values = [5, 10, 20]
        metrics = {}

        # Create ground truth sets for each user
        ground_truth_sets = ground_truth.groupby('user_id')['item_id'].apply(set).to_dict()

        # Calculate metrics for each k
        for k in k_values:
            precision_scores = []
            recall_scores = []
            ndcg_scores = []

            for user_id in ground_truth_sets.keys():
                # Get user's predictions
                user_predictions = predictions[predictions['user_id'] == user_id]

                if len(user_predictions) == 0:
                    continue

                # Get top-k recommendations - fix the nlargest call
                top_k_items = user_predictions.nlargest(n=k, columns="score")['item_id'].tolist()
                ground_truth_items = ground_truth_sets[user_id]

                # Calculate metrics
                if len(top_k_items) > 0:
                    # Precision@k
                    relevant_items = set(top_k_items) & ground_truth_items
                    precision = len(relevant_items) / len(top_k_items)
                    precision_scores.append(precision)

                    # Recall@k
                    recall = len(relevant_items) / len(ground_truth_items)
                    recall_scores.append(recall)

                    # NDCG@k
                    ndcg = RecommenderEvaluator._calculate_ndcg(
                        top_k_items, ground_truth_items, k
                    )
                    ndcg_scores.append(ndcg)

            # Average metrics
            if precision_scores:
                metrics[f'precision@{k}'] = np.mean(precision_scores)
                metrics[f'recall@{k}'] = np.mean(recall_scores)
                metrics[f'ndcg@{k}'] = np.mean(ndcg_scores)

        return metrics

    @staticmethod
    def _calculate_ndcg(recommendations: List[str],
                        ground_truth: set,
                        k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain."""

        def dcg(items, ground_truth, k):
            score = 0.0
            for i, item in enumerate(items[:k]):
                if item in ground_truth:
                    score += 1.0 / np.log2(i + 2)
            return score

        def idcg(ground_truth, k):
            # Ideal DCG - all relevant items at the top
            relevant_count = min(len(ground_truth), k)
            score = 0.0
            for i in range(relevant_count):
                score += 1.0 / np.log2(i + 2)
            return score

        dcg_score = dcg(recommendations, ground_truth, k)
        idcg_score = idcg(ground_truth, k)

        if idcg_score == 0:
            return 0.0

        return dcg_score / idcg_score

    @staticmethod
    def evaluate_rating_prediction(predictions: pd.DataFrame,
                                   ground_truth: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate rating prediction accuracy.
        
        Args:
            predictions: DataFrame with columns ['user_id', 'item_id', 'predicted_rating']
            ground_truth: DataFrame with columns ['user_id', 'item_id', 'rating']
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Merge predictions with ground truth
        merged = pd.merge(
            predictions, ground_truth,
            on=['user_id', 'item_id'],
            suffixes=('_pred', '_true')
        )

        if len(merged) == 0:
            return {'rmse': float('inf'), 'mae': float('inf'), 'n_predictions': 0}

        # Calculate metrics
        rmse = float(np.sqrt(mean_squared_error(merged['rating'], merged['predicted_rating'])))
        mae = float(mean_absolute_error(merged['rating'], merged['predicted_rating']))

        return {
            'rmse': rmse,
            'mae': mae,
            'n_predictions': len(merged)
        }

    @staticmethod
    def coverage_metrics(predictions: pd.DataFrame,
                         all_items: set) -> Dict[str, float]:
        """
        Calculate coverage metrics.
        
        Args:
            predictions: DataFrame with item recommendations
            all_items: Set of all possible items
            
        Returns:
            Dictionary with coverage metrics
        """
        recommended_items = set(predictions['item_id'].unique())

        catalog_coverage = len(recommended_items) / len(all_items)

        return {
            'catalog_coverage': catalog_coverage,
            'recommended_items': float(len(recommended_items)),
            'total_items': float(len(all_items))
        }

    @staticmethod
    def diversity_metrics(predictions: pd.DataFrame,
                          item_features: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Calculate diversity metrics.
        
        Args:
            predictions: DataFrame with recommendations grouped by user
            item_features: Optional item features for content-based diversity
            
        Returns:
            Dictionary with diversity metrics
        """
        from sklearn.metrics.pairwise import cosine_similarity

        diversity_scores = []

        for user_id in predictions['user_id'].unique():
            user_recs = predictions[predictions['user_id'] == user_id]['item_id'].tolist()

            if len(user_recs) < 2:
                continue

            # Calculate pairwise diversity
            if item_features is not None:
                # Content-based diversity
                user_item_features = item_features[item_features['item_id'].isin(user_recs)]
                if len(user_item_features) >= 2:
                    # Use numerical features for diversity calculation
                    numerical_cols = user_item_features.select_dtypes(include=[np.number]).columns
                    if len(numerical_cols) > 0:
                        feature_data = user_item_features[numerical_cols]
                        if hasattr(feature_data, 'to_numpy'):
                            feature_matrix = feature_data.to_numpy()
                        else:
                            feature_matrix = feature_data.values
                        similarity_matrix = cosine_similarity(feature_matrix)

                        # Average pairwise dissimilarity
                        n_items = len(similarity_matrix)
                        total_dissimilarity = 0
                        pairs = 0

                        for i in range(n_items):
                            for j in range(i + 1, n_items):
                                total_dissimilarity += (1 - similarity_matrix[i, j])
                                pairs += 1

                        if pairs > 0:
                            diversity_scores.append(total_dissimilarity / pairs)
            else:
                # Simple item diversity (unique items ratio)
                diversity_scores.append(len(set(user_recs)) / len(user_recs))

        avg_diversity = float(np.mean(diversity_scores)) if diversity_scores else 0.0
        std_diversity = float(np.std(diversity_scores)) if diversity_scores else 0.0

        return {
            'avg_diversity': avg_diversity,
            'std_diversity': std_diversity
        }

    @staticmethod
    def cross_validate_model(model: RecommenderProtocol,
                             interaction_data: pd.DataFrame,
                             n_folds: int = 5,
                             test_size: float = 0.2,
                             random_state: int = 42,
                             **fit_kwargs: Any) -> Dict[str, List[float]]:
        """
        Perform cross-validation on a recommendation model.
        
        Args:
            model: Recommender model instance
            interaction_data: DataFrame with interaction data
            n_folds: Number of cross-validation folds
            test_size: Size of a test set
            random_state: Random seed
            **fit_kwargs: Additional arguments for model.fit()
            
        Returns:
            Dictionary with metric scores across folds
        """
        from ..utils.preprocessing import DataPreprocessor

        np.random.seed(random_state)
        cv_metrics = {
            'precision@10': [],
            'recall@10': [],
            'ndcg@10': [],
            'training_time': []
        }

        for fold in range(n_folds):
            print(f"Cross-validation fold {fold + 1}/{n_folds}")

            # Split data
            train_data, test_data = DataPreprocessor.train_test_split(
                interaction_data,
                test_size=test_size,
                random_state=random_state + fold
            )

            # Train model
            start_time = time.time()
            model_copy = type(model)()
            model_copy.fit(train_data, **fit_kwargs)
            training_time = time.time() - start_time

            # Generate predictions
            test_users = test_data['user_id'].unique()
            predictions = model_copy.predict(test_users, n_recommendations=10)

            # Evaluate
            metrics = RecommenderEvaluator.evaluate_recommendations(
                predictions, test_data, k_values=[10]
            )

            # Store results
            cv_metrics['precision@10'].append(metrics.get('precision@10', 0.0))
            cv_metrics['recall@10'].append(metrics.get('recall@10', 0.0))
            cv_metrics['ndcg@10'].append(metrics.get('ndcg@10', 0.0))
            cv_metrics['training_time'].append(training_time)

        return cv_metrics

    @staticmethod
    def compare_models(models: Dict[str, RecommenderProtocol],
                       train_data: pd.DataFrame,
                       test_data: pd.DataFrame,
                       **fit_kwargs: Any) -> pd.DataFrame:
        """
        Compare multiple recommendation models.
        
        Args:
            models: Dictionary mapping model names to model instances
            train_data: Training data
            test_data: Test data
            **fit_kwargs: Additional arguments for model.fit()
            
        Returns:
            DataFrame with comparison results
        """
        results = []

        for model_name, model in models.items():
            print(f"Evaluating {model_name}...")

            # Train model
            start_time = time.time()
            model.fit(train_data, **fit_kwargs)
            training_time = time.time() - start_time

            # Generate predictions
            test_users = test_data['user_id'].unique()
            predictions = model.predict(test_users, n_recommendations=20)

            # Evaluate
            ranking_metrics = RecommenderEvaluator.evaluate_recommendations(
                predictions, test_data, k_values=[5, 10, 20]
            )

            # Combine results
            result = {
                'model': model_name,
                'training_time': training_time,
                **ranking_metrics
            }

            results.append(result)

        return pd.DataFrame(results)
