import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, Any, List
import tensorflow as tf
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.layers import Input, Embedding, Flatten, Dense, Concatenate, Dropout
from ..base.base_model import BaseModel


class NeuralCFModel(BaseModel):
    """
    Neural Collaborative Filtering model using deep learning with embeddings.
    Can work with any tabular data by treating it as user-item interactions.
    """

    def __init__(self, user_col: str = 'user_id', item_col: str = 'item_id', 
                 rating_col: str = 'rating', n_factors: int = 50, 
                 hidden_layers: List[int] = [64, 32], dropout_rate: float = 0.2, 
                 epochs: int = 20, batch_size: int = 256, **kwargs):
        """
        Initialize Neural Collaborative Filtering model.
        
        :param user_col: Name of the user column
        :param item_col: Name of the item column
        :param rating_col: Name of the rating/target column
        :param n_factors: Number of latent factors for embeddings
        :param hidden_layers: List of units in hidden dense layers
        :param dropout_rate: Dropout rate for regularization
        :param epochs: Number of training epochs
        :param batch_size: Batch size for training
        """
        super().__init__(user_col, item_col, rating_col, **kwargs)
        
        self.n_factors = n_factors
        self.hidden_layers = hidden_layers
        self.dropout_rate = dropout_rate
        self.epochs = epochs
        self.batch_size = batch_size
        
        # Model components
        self.model = None
        self.rating_scaler = MinMaxScaler(feature_range=(0, 1))
        self.min_rating = 0
        self.max_rating = 5

    def _create_rating_matrix(self, data: pd.DataFrame) -> csr_matrix:
        """
        Create user-item rating matrix from DataFrame.
        
        :param data: Input DataFrame
        :return: Sparse rating matrix
        """
        rating_matrix = data.pivot_table(
            index=self.user_col + '_encoded',
            columns=self.item_col + '_encoded',
            values=self.rating_col,
            fill_value=0
        )
        
        # Store rating bounds
        ratings = data[self.rating_col].to_numpy()
        self.min_rating = ratings.min()
        self.max_rating = ratings.max()
        
        # Scale ratings to [0, 1]
        rating_values = rating_matrix.values
        rating_values_scaled = self.rating_scaler.fit_transform(rating_values)
        
        return csr_matrix(rating_values_scaled)

    def _build_model(self):
        """
        Build the neural network model for collaborative filtering.
        """
        # Input layers
        user_input = Input(shape=(1,), name='user_input', dtype=tf.int32)
        item_input = Input(shape=(1,), name='item_input', dtype=tf.int32)
        
        # Embedding layers
        user_embedding = Embedding(self.n_users, self.n_factors, name='user_embedding')(user_input)
        item_embedding = Embedding(self.n_items, self.n_factors, name='item_embedding')(item_input)
        
        # Flatten embeddings
        user_vec = Flatten()(user_embedding)
        item_vec = Flatten()(item_embedding)
        
        # Concatenate user and item vectors
        concat = Concatenate()([user_vec, item_vec])
        
        # Hidden layers
        x = concat
        for units in self.hidden_layers:
            x = Dense(units, activation='relu')(x)
            x = Dropout(self.dropout_rate)(x)
        
        # Output layer
        output = Dense(1, activation='sigmoid')(x)
        
        # Build and compile model
        self.model = Model(inputs=[user_input, item_input], outputs=output)
        self.model.compile(optimizer='adam', loss='mse')

    def _train_impl(self, data: pd.DataFrame):
        """
        Train the Neural Collaborative Filtering model.
        
        :param data: Training data
        """
        # Prepare data
        user_ids = data[self.user_col + '_encoded'].values
        item_ids = data[self.item_col + '_encoded'].values
        ratings = data[self.rating_col].to_numpy()  # Convert to NumPy array explicitly
        
        # Scale ratings
        ratings_scaled = self.rating_scaler.fit_transform(ratings.reshape(-1, 1)).flatten()
        
        # Build model if not already built
        if self.model is None:
            self._build_model()

        if self.model is None:
            raise ValueError("Model must be built before training")
        
        # Train model
        self.model.fit(
            [user_ids, item_ids],
            ratings_scaled,
            batch_size=self.batch_size,
            epochs=self.epochs,
            verbose=str(1),
            validation_split=0.2
        )
        
        print(f"Neural CF trained with {self.n_factors} factors and {self.epochs} epochs")


    def _predict_impl(self, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        :param data: Input data for prediction
        :return: Predicted ratings
        """
        if self.model is None:
            raise ValueError("Model must be trained first")
        
        predictions = []
        for _, row in data.iterrows():
            user_encoded = int(row[self.user_col + '_encoded'])
            item_encoded = int(row[self.item_col + '_encoded'])
            
            # Handle out-of-bounds users/items
            if user_encoded >= self.n_users or item_encoded >= self.n_items:
                pred = self.global_mean
            else:
                result = self.model.predict([np.array([user_encoded]), np.array([item_encoded])], verbose=0)

                if isinstance(result, (list, np.ndarray)) and len(result) > 0:
                    pred_scaled = result[0][0]
                else:
                    print("Predict returned None or empty result")
                    pred_scaled = 0.0                

                pred = self.rating_scaler.inverse_transform([[pred_scaled]])[0][0]
            
            # Clip to rating bounds
            pred = np.clip(pred, self.min_rating, self.max_rating)
            predictions.append(pred)
        
        return np.array(predictions)


    def get_model_info(self) -> Dict[str, Any]:
        """
        Get detailed model information.
        """
        base_info = super().get_model_info()
        neural_info = {
            'n_factors': self.n_factors,
            'hidden_layers': self.hidden_layers,
            'dropout_rate': self.dropout_rate,
            'epochs': self.epochs,
            'batch_size': self.batch_size,
            'min_rating': self.min_rating,
            'max_rating': self.max_rating
        }
        base_info.update(neural_info)
        return base_info

    def explain_prediction(self, user_id: Any, item_id: Any) -> Dict[str, Any]:
        """
        Explain why a particular prediction was made.
        
        :param user_id: User identifier
        :param item_id: Item identifier
        :return: Explanation details
2.      """
        if not self.is_trained or self.model is None:
            raise ValueError("Model must be trained first")
        
        try:
            user_encoded = self.user_encoder.transform([user_id])[0]
            item_encoded = self.item_encoder.transform([item_id])[0]
            
            # Get prediction
            prediction_input = pd.DataFrame({
                self.user_col + '_encoded': [user_encoded],
                self.item_col + '_encoded': [item_encoded]
            })
            prediction = self._predict_impl(prediction_input)[0]
            
            return {
                'user_id': user_id,
                'item_id': item_id,
                'prediction': float(prediction),
                'explanation': 'Neural CF prediction based on learned embeddings and dense layers'
            }
        
        except (ValueError, IndexError):
            return {
                'user_id': user_id,
                'item_id': item_id,
                'prediction': float(self.global_mean),
                'explanation': 'Unknown user or item, using global mean'
            }
