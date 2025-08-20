from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ModelStatus(str, Enum):
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    VALIDATING = "validating"


class ModelType(str, Enum):
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    DEEP_LEARNING = "deep_learning"


class AlgorithmType(str, Enum):
    ALS = "als"
    BPR = "bpr"
    NCF = "ncf"
    TFIDF = "tfidf"
    FEATURE_BASED = "feature_based"
    MATRIX_FACTORIZATION = "matrix_factorization"
    NEURAL_COLLABORATIVE = "neural_collaborative"


# Base Model Configuration Schemas
class BaseModelConfig(BaseModel):
    """Base configuration for all models"""

    random_state: int = Field(default=42, description="Random seed for reproducibility")

    class Config:
        extra = "allow"  # Allow additional fields for model-specific parameters


class ALSModelConfig(BaseModelConfig, BaseModel):
    """Configuration for ALS (Alternating Least Squares) model"""

    factors: int = Field(
        default=100, ge=1, le=1000, description="Number of latent factors"
    )
    regularization: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Regularization parameter"
    )
    iterations: int = Field(
        default=15, ge=1, le=100, description="Number of ALS iterations"
    )

    @field_validator("factors")
    @classmethod
    def validate_factors(cls, v: int) -> int:
        """
        Validate the number of factors for ALS.
        """
        if v <= 0:
            raise ValueError("factors must be positive")
        return v


class BPRModelConfig(BaseModelConfig):
    """Configuration for BPR (Bayesian Personalized Ranking) model"""

    factors: int = Field(
        default=100, ge=1, le=1000, description="Number of latent factors"
    )
    learning_rate: float = Field(
        default=0.05, ge=0.001, le=1.0, description="Learning rate for SGD"
    )
    regularization: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Regularization parameter"
    )
    iterations: int = Field(
        default=100, ge=1, le=1000, description="Number of training iterations"
    )

    @field_validator("learning_rate")
    @classmethod
    def validate_learning_rate(cls, v: float) -> float:
        """
        Validate the learning rate for BPR.
        """
        if v <= 0:
            raise ValueError("learning_rate must be positive")
        return v


class NCFModelConfig(BaseModelConfig):
    """Configuration for NCF (Neural Collaborative Filtering) model"""

    embedding_size: int = Field(
        default=50, ge=8, le=512, description="Size of user and item embeddings"
    )
    hidden_units: List[int] = Field(
        default=[128, 64], description="Hidden layer sizes for MLP component"
    )
    dropout_rate: float = Field(
        default=0.2, ge=0.0, le=0.9, description="Dropout rate for regularization"
    )
    learning_rate: float = Field(
        default=0.001, ge=0.0001, le=0.1, description="Learning rate for optimizer"
    )
    epochs: int = Field(
        default=50, ge=1, le=500, description="Number of training epochs"
    )
    batch_size: int = Field(
        default=256, ge=16, le=2048, description="Batch size for training"
    )
    negative_sampling: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Number of negative samples per positive sample",
    )

    @field_validator("hidden_units")
    @classmethod
    def validate_hidden_units(cls, v: List[int]) -> List[int]:
        """
        Validate the hidden units for NCF.
        """
        if not v or any(unit <= 0 for unit in v):
            raise ValueError("hidden_units must be non-empty with positive values")
        return v


class TFIDFModelConfig(BaseModelConfig):
    """Configuration for a TF-IDF Content-Based model"""

    max_features: int = Field(
        default=5000,
        ge=100,
        le=50000,
        description="Maximum number of features for TF-IDF",
    )
    min_df: int = Field(
        default=2, ge=1, description="Minimum document frequency for TF-IDF"
    )
    max_df: float = Field(
        default=0.8, ge=0.1, le=1.0, description="Maximum document frequency for TF-IDF"
    )
    stop_words: str = Field(default="english", description="Stop words to remove")
    ngram_range: tuple = Field(default=(1, 2), description="N-gram range for TF-IDF")

    @field_validator("ngram_range")
    @classmethod
    def validate_ngram_range(cls, v: tuple) -> tuple:
        """
        Validate the n-gram range for TF-IDF.
        """
        if len(v) != 2 or v[0] > v[1] or v[0] < 1:
            raise ValueError(
                "ngram_range must be a tuple of two positive integers where first <= second"
            )
        return v


class FeatureBasedModelConfig(BaseModelConfig):
    """Configuration for a Feature-Based Content model"""

    categorical_features: Optional[List[str]] = Field(
        default=None, description="List of categorical feature column names"
    )
    numerical_features: Optional[List[str]] = Field(
        default=None, description="List of numerical feature column names"
    )
    feature_weights: Optional[Dict[str, float]] = Field(
        default=None, description="Dictionary mapping feature names to weights"
    )
    similarity_metric: str = Field(
        default="cosine", description="Similarity metric to use"
    )
    normalize_features: bool = Field(
        default=True, description="Whether to normalize numerical features"
    )

    @field_validator("similarity_metric")
    @classmethod
    def validate_similarity_metric(cls, v: str) -> str:
        """
        Validate the similarity metric for Feature-Based models.
        """
        valid_metrics = ["cosine", "euclidean", "manhattan", "pearson"]
        if v not in valid_metrics:
            raise ValueError(f"similarity_metric must be one of {valid_metrics}")
        return v


# Model Training Request Schemas
class ModelTrainingRequest(BaseModel):
    """Request schema for training a model"""

    model_name: str = Field(..., description="Unique name for the model")
    algorithm: AlgorithmType = Field(..., description="Algorithm to use")
    config: Union[
        ALSModelConfig,
        BPRModelConfig,
        NCFModelConfig,
        TFIDFModelConfig,
        FeatureBasedModelConfig,
    ] = Field(..., description="Model-specific configuration")
    interaction_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Reference to interaction data or data itself"
    )
    user_features: Optional[Dict[str, Any]] = Field(
        default=None, description="Reference to user features or data itself"
    )
    item_features: Optional[Dict[str, Any]] = Field(
        default=None, description="Reference to item features or data itself"
    )
    validation_split: float = Field(
        default=0.2,
        ge=0.0,
        le=0.5,
        description="Fraction of data to use for validation",
    )

    class Config:
        schema_extra = {
            "example": {
                "model_name": "als_movie_recommender",
                "algorithm": "als",
                "config": {
                    "factors": 100,
                    "regularization": 0.01,
                    "iterations": 20,
                    "random_state": 42,
                },
                "validation_split": 0.2,
            }
        }


class ModelTrainingResult(BaseModel):
    """Result schema for model training"""

    model_id: str = Field(..., description="ID of the trained model")
    status: str = Field(..., description="Training status")
    metrics: Dict[str, float] = Field(..., description="Training metrics")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "status": self.status,
            "metrics": self.metrics,
        }


class ModelInfo(BaseModel):
    """Information about a trained model"""

    model_id: str = Field(..., description="Unique model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    message: str = Field(..., description="Description or message about the model")
    algorithm: AlgorithmType = Field(default=None, description="Algorithm used")
    model_type: ModelType = Field(
        default=None, description="Type of recommendation model"
    )
    status: ModelStatus = Field(..., description="Current model status")
    created_at: datetime = Field(default=None, description="When the model was created")
    updated_at: datetime = Field(
        default=None, description="When the model was last updated"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Model performance metrics"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Model configuration"
    )
    training_started_at: Optional[datetime] = Field(
        default=None, description="When the training started"
    )
    training_completed_at: Optional[datetime] = Field(
        default=None, description="When the training completed"
    )
    training_time: Optional[int] = Field(
        default=60, description="Total training time in seconds"
    )
    query_string: Optional[str] = Field(
        default=None, description="Query string used for database models"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "message": self.message,
            "algorithm": self.algorithm,
            "model_type": self.model_type,
            "status": self.status,
            "created_at": (
                self.created_at.isoformat()
                if isinstance(self.created_at, datetime)
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if isinstance(self.updated_at, datetime)
                else None
            ),
            "metrics": self.metrics,
            "config": self.config,
            "training_time": self.training_time,
            "training_started_at": (
                self.training_started_at.isoformat()
                if self.training_started_at
                else None
            ),
            "training_completed_at": (
                self.training_completed_at.isoformat()
                if self.training_completed_at
                else None
            ),
            "query_string": self.query_string,
        }

    class Config:
        schema_extra = {
            "example": {
                "model_id": "model_123",
                "model_name": "Movie ALS Recommender",
                "message": "A collaborative filtering model for movie recommendations",
                "algorithm": "als",
                "model_type": "collaborative",
                "status": "completed",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:35:00Z",
                "training_time": 45.5,
                "metrics": {"rmse": 0.85, "mae": 0.67},
                "config": {"factors": 100, "regularization": 0.01},
            }
        }


class ModelPredictResult(BaseModel):
    """Result schema for model predictions"""

    model_id: str = Field(..., description="ID of the recommendation model")
    user_id: str = Field(..., description="ID of the user")
    predictions: Dict = Field(
        ...,
        description="Predicted recommendations with item_id and score",
    )
    datetime: str = Field(
        ...,
        description="Timestamp of the prediction",
    )
    status: ModelStatus = Field(..., description="Status of the prediction")
    n_recommendations: int = Field(
        default=10, description="Number of recommendations returned"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "user_id": self.user_id,
            "predictions": self.predictions,
            "datetime": self.datetime,
            "status": self.status,
            "n_recommendations": self.n_recommendations,
        }


class ModelPredictScoresResult(BaseModel):
    """Result schema for specific user-item score predictions"""

    model_id: str = Field(..., description="ID of the recommendation model")
    results: List[Dict[str, Union[str, float]]] = Field(
        ...,
        description="Prediction results with user_id, item_id, and score",
    )
    datetime: str = Field(
        ...,
        description="Timestamp of the prediction",
    )
    status: ModelStatus = Field(..., description="Status of the prediction")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "results": self.results,
            "datetime": self.datetime,
            "status": self.status,
        }


class ModelPredictRequest(BaseModel):
    """Request schema for getting recommendations"""

    user_ids: Union[str, List[str]] = Field(
        ..., description="User ID(s) to get recommendations for"
    )
    n_recommendations: int = Field(
        default=10, ge=1, le=100, description="Number of recommendations per user"
    )
    exclude_seen: bool = Field(
        default=True,
        description="Whether to exclude items user has already interacted with",
    )

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [v]
        if not v:
            raise ValueError("user_ids cannot be empty")
        return v


class ModelScorePredictRequest(BaseModel):
    """Request schema for predicting specific user-item scores"""

    user_ids: Union[str, List[str]] = Field(..., description="User ID(s)")
    item_ids: Union[str, List[str]] = Field(..., description="Item ID(s)")

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("item_ids")
    @classmethod
    def validate_item_ids(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

    @field_validator("item_ids")
    @classmethod
    def validate_equal_length(cls, v, values):
        if "user_ids" in values:
            user_ids = values["user_ids"]
            if isinstance(user_ids, str):
                user_ids = [user_ids]
            if len(v) != len(user_ids):
                raise ValueError("user_ids and item_ids must have the same length")
        return v


class ModelEvaluationResult(BaseModel):
    """Result schema for model evaluation"""

    model_id: str = Field(..., description="ID of the evaluated model")
    metrics: Dict[str, float] = Field(..., description="Evaluation metrics")
    evaluation_time: float = Field(
        ..., description="Time taken for evaluation in seconds"
    )
    datetime: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Evaluation timestamp",
    )

    class Config:
        schema_extra = {
            "example": {
                "model_id": "model_123",
                "metrics": {
                    "precision_at_10": 0.15,
                    "recall_at_10": 0.25,
                    "ndcg_at_10": 0.35,
                    "rmse": 0.85,
                },
                "evaluation_time": 12.5,
                "datetime": "2025-01-15T11:00:00Z",
            }
        }


class ModelListResponse(BaseModel):
    """Response schema for listing models"""

    models: List[ModelInfo] = Field(..., description="List of available models")
    total: int = Field(..., description="Total number of models")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Number of models per page")


class ModelTrainingStatus(BaseModel):
    """Status of model training"""

    model_id: str = Field(..., description="Model identifier")
    status: ModelStatus = Field(..., description="Current training status")
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Training progress percentage"
    )
    current_epoch: Optional[int] = Field(
        default=None, description="Current epoch (for iterative models)"
    )
    total_epochs: Optional[int] = Field(
        default=None, description="Total epochs to train"
    )
    current_loss: Optional[float] = Field(
        default=None, description="Current training loss"
    )
    message: Optional[str] = Field(
        default=None, description="Status message or error description"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Training start time"
    )
    estimated_completion: Optional[datetime] = Field(
        default=None, description="Estimated completion time"
    )


# Error Response Schemas
class ErrorResponse(BaseModel):
    """Error response schema"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp",
    )


# Model Comparison Schema
class ModelComparison(BaseModel):
    """Schema for comparing multiple models"""

    models: List[str] = Field(..., description="List of model IDs to compare")
    metrics: List[str] = Field(..., description="Metrics to compare")
    test_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Test data for comparison"
    )


class ModelComparisonResult(BaseModel):
    """Result of model comparison"""

    comparison_id: str = Field(..., description="Unique comparison identifier")
    models: Dict[str, Dict[str, float]] = Field(
        ..., description="Model performance metrics"
    )
    best_model: str = Field(..., description="ID of the best performing model")
    comparison_time: float = Field(..., description="Time taken for comparison")
    datetime: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Comparison timestamp",
    )


# Hyperparameter Tuning Schemas
class HyperparameterRange(BaseModel):
    """Range for hyperparameter tuning"""

    min_value: Union[int, float] = Field(..., description="Minimum value")
    max_value: Union[int, float] = Field(..., description="Maximum value")
    step: Optional[Union[int, float]] = Field(default=None, description="Step size")
    values: Optional[List[Union[int, float, str]]] = Field(
        default=None, description="Specific values to try"
    )


class HyperparameterTuningRequest(BaseModel):
    """Request for hyperparameter tuning"""

    algorithm: AlgorithmType = Field(..., description="Algorithm to tune")
    parameter_ranges: Dict[str, HyperparameterRange] = Field(
        ..., description="Parameter ranges to search"
    )
    cv_folds: int = Field(
        default=5, ge=2, le=10, description="Number of cross-validation folds"
    )
    scoring_metric: str = Field(default="rmse", description="Metric to optimize")
    n_trials: int = Field(
        default=100, ge=10, le=1000, description="Number of optimization trials"
    )


class HyperparameterTuningResult(BaseModel):
    """Result of hyperparameter tuning"""

    tuning_id: str = Field(..., description="Unique tuning job identifier")
    best_params: Dict[str, Any] = Field(..., description="Best hyperparameters found")
    best_score: float = Field(..., description="Best score achieved")
    all_trials: List[Dict[str, Any]] = Field(..., description="All trials performed")
    tuning_time: float = Field(..., description="Total tuning time in seconds")
    datetime: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Tuning timestamp",
    )
