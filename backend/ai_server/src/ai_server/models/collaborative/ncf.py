"""
Neural Collaborative Filtering (NCF) Implementation
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Tuple
import time

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

from ..base_model import BaseRecommender


class NCFRecommender(BaseRecommender):
    """
    Neural Collaborative Filtering model.
    
    Combines Generalized Matrix Factorization (GMF) and Multi-Layer Perceptron (MLP)
    to learn user-item interactions using deep learning.
    
    Parameters:
    -----------
    embedding_size : int, default=50
        Size of user and item embeddings
    hidden_units : list, default=[128, 64]
        Hidden layer sizes for MLP component
    dropout_rate : float, default=0.2
        Dropout rate for regularization
    learning_rate : float, default=0.001
        Learning rate for optimizer
    epochs : int, default=50
        Number of training epochs
    batch_size : int, default=256
        Batch size for training
    negative_sampling : int, default=4
        Number of negative samples per positive sample
    random_state : int, default=42
        Random seed for reproducibility
    """

    def __init__(self, embedding_size: int = 50, hidden_units: List[int] = [128, 64],
                 dropout_rate: float = 0.2, learning_rate: float = 0.001,
                 epochs: int = 50, batch_size: int = 256, negative_sampling: int = 4,
                 random_state: int = 42, **kwargs):

        if not HAS_TENSORFLOW:
            raise ImportError("TensorFlow is required for NCF model. Please install tensorflow>=2.0")

        super().__init__(embedding_size=embedding_size, hidden_units=hidden_units,
                         dropout_rate=dropout_rate, learning_rate=learning_rate,
                         epochs=epochs, batch_size=batch_size,
                         negative_sampling=negative_sampling,
                         random_state=random_state, **kwargs)

        self.embedding_size = embedding_size
        self.hidden_units = hidden_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.negative_sampling = negative_sampling
        self.random_state = random_state

        # Set random seeds
        np.random.seed(random_state)
        tf.random.set_seed(random_state)

    def fit(self, interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None) -> 'NCFRecommender':
        """
        Train the NCF model.
        
        Args:
            interaction_data: DataFrame with columns ['user_id', 'item_id'] and optionally 'rating'
            user_features: Not used in basic NCF (for API consistency)
            item_features: Not used in basic NCF (for API consistency)
            
        Returns:
            Self for method chaining
        """
        self._validate_input(interaction_data)

        print(f"Training NCF model with {len(interaction_data)} interactions...")
        start_time = time.time()

        # Encode users and items
        data = self._encode_users_items(interaction_data.copy())

        self.n_users = len(self.user_encoder.classes_)
        self.n_items = len(self.item_encoder.classes_)

        # Prepare training data with negative sampling
        train_data = self._prepare_training_data(data)

        # Build model
        self.model = self._build_model()

        # Compile model
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        # Train model
        history = self.model.fit(
            [train_data['user_idx'], train_data['item_idx']],
            train_data['rating'],
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=0.2,
            verbose=1
        )

        training_time = time.time() - start_time

        self.training_history = [
            {'epoch': i, 'loss': history.history['loss'][i],
             'val_loss': history.history['val_loss'][i]}
            for i in range(len(history.history['loss']))
        ]

        self.metrics = {
            'final_loss': history.history['loss'][-1],
            'final_val_loss': history.history['val_loss'][-1],
            'training_time': training_time,
            'n_users': self.n_users,
            'n_items': self.n_items
        }

        self.is_fitted = True
        print(f"Training completed in {training_time:.2f}s")

        return self

    def _build_model(self) -> keras.Model:
        """Build the NCF neural network architecture."""
        # Input layers
        user_input = keras.Input(shape=(), name='user_id')
        item_input = keras.Input(shape=(), name='item_id')

        # GMF part
        gmf_user_embedding = layers.Embedding(
            self.n_users, self.embedding_size, name='gmf_user_embedding'
        )(user_input)
        gmf_item_embedding = layers.Embedding(
            self.n_items, self.embedding_size, name='gmf_item_embedding'
        )(item_input)

        gmf_user_vec = layers.Flatten()(gmf_user_embedding)
        gmf_item_vec = layers.Flatten()(gmf_item_embedding)
        gmf_output = layers.Multiply()([gmf_user_vec, gmf_item_vec])

        # MLP part
        mlp_user_embedding = layers.Embedding(
            self.n_users, self.embedding_size, name='mlp_user_embedding'
        )(user_input)
        mlp_item_embedding = layers.Embedding(
            self.n_items, self.embedding_size, name='mlp_item_embedding'
        )(item_input)

        mlp_user_vec = layers.Flatten()(mlp_user_embedding)
        mlp_item_vec = layers.Flatten()(mlp_item_embedding)
        mlp_concat = layers.Concatenate()([mlp_user_vec, mlp_item_vec])

        # MLP layers
        mlp_output = mlp_concat
        for units in self.hidden_units:
            mlp_output = layers.Dense(units, activation='relu')(mlp_output)
            mlp_output = layers.Dropout(self.dropout_rate)(mlp_output)

        # Combine GMF and MLP
        concat_output = layers.Concatenate()([gmf_output, mlp_output])

        # Final prediction layer
        prediction = layers.Dense(1, activation='sigmoid', name='prediction')(concat_output)

        model = keras.Model(inputs=[user_input, item_input], outputs=prediction)

        return model

    def _prepare_training_data(self, data: pd.DataFrame) -> dict:
        """Prepare training data with negative sampling."""
        # Create positive samples
        positive_samples = data[['user_idx', 'item_idx']].copy()
        positive_samples['rating'] = 1.0

        # Create negative samples
        negative_samples = []
        user_items = data.groupby('user_idx')['item_idx'].apply(set).to_dict()

        for user_idx in data['user_idx'].unique():
            user_positive_items = user_items[user_idx]

            # Sample negative items for this user
            n_negative = len(user_positive_items) * self.negative_sampling

            for _ in range(n_negative):
                neg_item = np.random.randint(0, self.n_items)
                while neg_item in user_positive_items:
                    neg_item = np.random.randint(0, self.n_items)

                negative_samples.append({
                    'user_idx': user_idx,
                    'item_idx': neg_item,
                    'rating': 0.0
                })

        negative_df = pd.DataFrame(negative_samples)

        # Combine positive and negative samples
        all_samples = pd.concat([positive_samples, negative_df], ignore_index=True)
        all_samples = all_samples.sample(frac=1).reset_index(drop=True)  # Shuffle

        return {
            'user_idx': all_samples['user_idx'].values,
            'item_idx': all_samples['item_idx'].values,
            'rating': all_samples['rating'].values
        }

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

            # Create input for all items
            user_input = np.full(self.n_items, user_idx)
            item_input = np.arange(self.n_items)

            # Predict scores
            scores = self.model.predict([user_input, item_input], verbose=0).flatten()

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

        user_indices = []
        item_indices = []

        for user_id, item_id in zip(user_ids, item_ids):
            try:
                user_idx = self.user_encoder.transform([user_id])[0]
                item_idx = self.item_encoder.transform([item_id])[0]
                user_indices.append(user_idx)
                item_indices.append(item_idx)
            except ValueError:
                # Unknown user or item
                user_indices.append(0)  # Default to first user/item
                item_indices.append(0)

        # Predict scores
        scores = self.model.predict([np.array(user_indices), np.array(item_indices)], verbose=0)

        return scores.flatten()
