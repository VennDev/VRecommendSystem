"""
Data preprocessing utilities for recommendation systems.
"""
import loguru
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from sklearn.model_selection import train_test_split


class DataPreprocessor:
    """
    Utility class for preprocessing recommendation data.
    
    Provides methods for splitting data, handling missing values,
    filtering sparse users/items, and other common preprocessing tasks.
    """

    @staticmethod
    def train_test_split(interaction_data: pd.DataFrame,
                         test_size: float = 0.2,
                         random_state: int = 42,
                         stratify_by_user: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split interaction data into train and test sets.
        
        Args:
            interaction_data: DataFrame with user-item interactions
            test_size: Proportion of data for testing
            random_state: Random seed
            stratify_by_user: Whether to stratify split by users
            
        Returns:
            Tuple of (train_data, test_data)
        """
        if stratify_by_user:
            # Ensure each user has at least one interaction in a train set
            train_list = []
            test_list = []

            for user_id in interaction_data['user_id'].unique():
                user_data = interaction_data[interaction_data['user_id'] == user_id]

                if len(user_data) == 1:
                    # Single interaction goes to train
                    train_list.append(user_data)
                else:
                    # Split user's interactions
                    user_train, user_test = train_test_split(
                        user_data, test_size=test_size, random_state=random_state
                    )
                    train_list.append(user_train)
                    test_list.append(user_test)

            train_data = pd.concat(train_list, ignore_index=True)
            test_data = pd.concat(test_list, ignore_index=True) if test_list else pd.DataFrame()

        else:
            # Simple random split
            train_data, test_data = train_test_split(
                interaction_data, test_size=test_size, random_state=random_state
            )

        return train_data, test_data

    @staticmethod
    def filter_sparse_users_items(interaction_data: pd.DataFrame,
                                  min_user_interactions: int = 5,
                                  min_item_interactions: int = 5) -> pd.DataFrame:
        """
        Filter out sparse users and items.
        
        Args:
            interaction_data: DataFrame with user-item interactions
            min_user_interactions: Minimum interactions per user
            min_item_interactions: Minimum interactions per item
            
        Returns:
            Filtered DataFrame
        """
        original_size = len(interaction_data)

        # Iteratively filter until no more changes
        while True:
            # Filter users
            user_counts = interaction_data['user_id'].value_counts()
            valid_users = user_counts[user_counts >= min_user_interactions].index
            interaction_data = interaction_data[interaction_data['user_id'].isin(valid_users)]

            # Filter items
            item_counts = interaction_data['item_id'].value_counts()
            valid_items = item_counts[item_counts >= min_item_interactions].index
            new_data = interaction_data[interaction_data['item_id'].isin(valid_items)]

            # Check if any changes were made
            if len(new_data) == len(interaction_data):
                break

            interaction_data = new_data

        loguru.logger.info(f"Filtered data: {original_size} -> {len(interaction_data)} interactions")
        loguru.logger.info(f"Users: {interaction_data['user_id'].nunique()}")
        loguru.logger.info(f"Items: {interaction_data['item_id'].nunique()}")

        return interaction_data.reset_index(drop=True)

    @staticmethod
    def handle_implicit_feedback(interaction_data: pd.DataFrame,
                                 rating_threshold: float = 3.5) -> pd.DataFrame:
        """
        Convert explicit ratings to implicit feedback.
        
        Args:
            interaction_data: DataFrame with rating column
            rating_threshold: Threshold for positive feedback
            
        Returns:
            DataFrame with binary feedback
        """
        if 'rating' not in interaction_data.columns:
            # Already implicit - add default positive rating
            interaction_data = interaction_data.copy()
            interaction_data['rating'] = 1.0
            return interaction_data

        # Convert to binary
        interaction_data = interaction_data.copy()
        interaction_data['rating'] = (interaction_data['rating'] >= rating_threshold).astype(float)

        # Filter only positive feedback
        return interaction_data[interaction_data['rating'] > 0].reset_index(drop=True)

    @staticmethod
    def create_negative_samples(interaction_data: pd.DataFrame,
                                negative_ratio: float = 1.0,
                                random_state: int = 42) -> pd.DataFrame:
        """
        Create negative samples for implicit feedback data.
        
        Args:
            interaction_data: DataFrame with positive interactions
            negative_ratio: Ratio of negative to positive samples
            random_state: Random seed
            
        Returns:
            DataFrame with positive and negative samples
        """
        np.random.seed(random_state)

        # Get all users and items
        all_users = interaction_data['user_id'].unique()
        all_items = interaction_data['item_id'].unique()

        # Create a user-item interaction set for quick lookup
        positive_pairs = set(zip(interaction_data['user_id'], interaction_data['item_id']))

        # Generate negative samples
        negative_samples = []
        n_negative = int(len(interaction_data) * negative_ratio)

        while len(negative_samples) < n_negative:
            user_id = np.random.choice(all_users)
            item_id = np.random.choice(all_items)

            if (user_id, item_id) not in positive_pairs:
                negative_samples.append({
                    'user_id': user_id,
                    'item_id': item_id,
                    'rating': 0.0
                })

        # Combine positive and negative samples
        negative_df = pd.DataFrame(negative_samples)
        combined_data = pd.concat([interaction_data, negative_df], ignore_index=True)

        return combined_data.sample(frac=1, random_state=random_state).reset_index(drop=True)

    @staticmethod
    def normalize_ratings(interaction_data: pd.DataFrame,
                          method: str = 'min_max') -> pd.DataFrame:
        """
        Normalize rating values.
        
        Args:
            interaction_data: DataFrame with rating column
            method: Normalization method ('min_max', 'z_score', 'unit')
            
        Returns:
            DataFrame with normalized ratings
        """
        if 'rating' not in interaction_data.columns:
            return interaction_data

        interaction_data = interaction_data.copy()
        ratings = interaction_data['rating'].values

        if method == 'min_max':
            min_rating = ratings.min()
            max_rating = ratings.max()
            if max_rating > min_rating:
                interaction_data['rating'] = (ratings - min_rating) / (max_rating - min_rating)

        elif method == 'z_score':
            mean_rating = ratings.mean()
            std_rating = ratings.std()
            if std_rating > 0:
                interaction_data['rating'] = (ratings - mean_rating) / std_rating

        elif method == 'unit':
            norm = np.linalg.norm(ratings)
            if norm > 0:
                interaction_data['rating'] = ratings / norm

        else:
            raise ValueError(f"Unknown normalization method: {method}")

        return interaction_data

    @staticmethod
    def create_temporal_split(interaction_data: pd.DataFrame,
                              timestamp_col: str = 'timestamp',
                              test_days: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data based on temporal order.
        
        Args:
            interaction_data: DataFrame with timestamp column
            timestamp_col: Name of timestamp column
            test_days: Number of days for a test set
            
        Returns:
            Tuple of (train_data, test_data)
        """
        if timestamp_col not in interaction_data.columns:
            raise ValueError(f"Timestamp column '{timestamp_col}' not found")

        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(interaction_data[timestamp_col]):
            interaction_data = interaction_data.copy()
            interaction_data[timestamp_col] = pd.to_datetime(interaction_data[timestamp_col])

        # Find split point
        max_timestamp = interaction_data[timestamp_col].max()
        split_point = max_timestamp - pd.Timedelta(days=test_days)

        # Split data
        train_data = interaction_data[interaction_data[timestamp_col] <= split_point]
        test_data = interaction_data[interaction_data[timestamp_col] > split_point]

        return train_data.reset_index(drop=True), test_data.reset_index(drop=True)

    @staticmethod
    def validate_data_format(interaction_data: pd.DataFrame,
                             required_columns=None) -> bool:
        """
        Validate that interaction data has the required format.
        
        Args:
            interaction_data: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            True if valid, raises ValueError if not
        """
        # Check required columns
        if required_columns is None:
            required_columns = ['user_id', 'item_id']
        missing_columns = [col for col in required_columns if col not in interaction_data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check for empty data
        if interaction_data.empty:
            raise ValueError("Interaction data is empty")

        # Check for null values in required columns
        for col in required_columns:
            if interaction_data[col].isnull().any():
                raise ValueError(f"Column '{col}' contains null values")

        # Check data types
        if not pd.api.types.is_object_dtype(interaction_data['user_id']) and \
                not pd.api.types.is_string_dtype(interaction_data['user_id']):
            if not pd.api.types.is_integer_dtype(interaction_data['user_id']):
                loguru.logger.warning("Warning: user_id should be string/object or integer type")

        if not pd.api.types.is_object_dtype(interaction_data['item_id']) and \
                not pd.api.types.is_string_dtype(interaction_data['item_id']):
            if not pd.api.types.is_integer_dtype(interaction_data['item_id']):
                loguru.logger.warning("Warning: item_id should be string/object or integer type")

        return True

    @staticmethod
    def get_data_statistics(interaction_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Get descriptive statistics about the interaction data.
        
        Args:
            interaction_data: DataFrame with user-item interactions
            
        Returns:
            Dictionary with data statistics
        """
        stats = {
            'n_interactions': len(interaction_data),
            'n_users': interaction_data['user_id'].nunique(),
            'n_items': interaction_data['item_id'].nunique(),
            'sparsity': 1 - (len(interaction_data) / (
                    interaction_data['user_id'].nunique() * interaction_data['item_id'].nunique())),
            'avg_interactions_per_user': len(interaction_data) / interaction_data['user_id'].nunique(),
            'avg_interactions_per_item': len(interaction_data) / interaction_data['item_id'].nunique(),
        }

        # User statistics
        user_counts = interaction_data['user_id'].value_counts()
        stats.update({
            'min_user_interactions': user_counts.min(),
            'max_user_interactions': user_counts.max(),
            'median_user_interactions': user_counts.median(),
        })

        # Item statistics
        item_counts = interaction_data['item_id'].value_counts()
        stats.update({
            'min_item_interactions': item_counts.min(),
            'max_item_interactions': item_counts.max(),
            'median_item_interactions': item_counts.median(),
        })

        # Rating statistics if available
        if 'rating' in interaction_data.columns:
            ratings = interaction_data['rating']
            stats.update({
                'min_rating': ratings.min(),
                'max_rating': ratings.max(),
                'mean_rating': ratings.mean(),
                'std_rating': ratings.std(),
            })

        return stats
