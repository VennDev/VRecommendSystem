import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

import loguru
import pandas as pd

# Import models from the models folder
from ..models.collaborative.als import ALSRecommender
from ..models.collaborative.bpr import BPRRecommender
from ..models.collaborative.ncf import NCFRecommender
from ..models.content.tfidf import TFIDFRecommender
from ..models.content.feature_based import FeatureBasedRecommender
from ..models.base_model import BaseRecommender

# Import evaluation utilities
from ..models.utils.evaluation import RecommenderEvaluator
from ..models.utils.preprocessing import DataPreprocessor

# Schemas
from ..schemas.model_schemas import (
    ModelTrainingResult,
    ModelPredictResult,
    ModelPredictScoresResult,
    ModelStatus,
)


class ModelService:
    """
    Simplified service class for managing recommendation models.
    Handles training, loading, saving, and prediction operations using only DataFrames.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # In-memory model cache
        self.loaded_models: Dict[str, BaseRecommender] = {}

        # Model configuration storage
        self.model_configs: Dict[str, Dict[str, Any]] = {}

        # Initialize model registry
        self.model_registry: Dict[str, Type[BaseRecommender]] = {
            "als": ALSRecommender,
            "bpr": BPRRecommender,
            "ncf": NCFRecommender,
            "tfidf": TFIDFRecommender,
            "feature": FeatureBasedRecommender,
        }

    def get_model_class(self, algorithm: str) -> Type[BaseRecommender]:
        """Get model class by algorithm name."""
        if algorithm not in self.model_registry:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. Available: {list(self.model_registry.keys())}"
            )
        return self.model_registry[algorithm]

    def train_model(
            self,
            model_id: str,
            model_name: str,
            algorithm: str,
            message: str,
            training_time: float,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> ModelTrainingResult:
        """
        Train a model from DataFrames.

        Args:
            model_id: Unique identifier for the model
            model_name: User-friendly name for the model
            algorithm: Algorithm name (als, bpr, ncf, tfidf, feature)
            interaction_data: Interaction data DataFrame
            user_features: Optional user features DataFrame
            item_features: Optional item features DataFrame
            hyperparameters: Model hyperparameters
            message: Description or message about the model
            training_time: Retrain interval in seconds (how often to retrain the model)

        Returns:
            ModelTrainingResult object with training details
        """
        try:
            loguru.logger.info(
                f"Starting training for model {model_id} with algorithm {algorithm}"
            )

            # Validate interaction data
            DataPreprocessor.validate_data_format(interaction_data)
            loguru.logger.info(f"Interaction data shape: {interaction_data.shape}")

            # Log features if provided
            if user_features is not None:
                loguru.logger.info(f"User features shape: {user_features.shape}")
            if item_features is not None:
                loguru.logger.info(f"Item features shape: {item_features.shape}")

            # Create model configuration
            start_time = datetime.now()
            config = {
                "model_id": model_id,
                "model_name": model_name,
                "message": message,
                "algorithm": algorithm,
                "hyperparameters": hyperparameters or {},
                "created_at": start_time.isoformat(),
                "training_started_at": start_time.isoformat(),
                "status": ModelStatus.TRAINING,
                "model_path": str(self.models_dir / f"{model_id}.pkl"),
                "training_time": training_time,  # Retrain interval in seconds
            }

            # Store config
            self.model_configs[model_id] = config

            # Initialize model
            model_class = self.get_model_class(algorithm)
            model = model_class(**config["hyperparameters"])

            # Train model
            model.fit(interaction_data, user_features, item_features)
            actual_training_duration = (datetime.now() - start_time).total_seconds()

            # Save trained model
            model_path = config["model_path"]
            model.save(model_path)

            # Update configuration
            config["status"] = ModelStatus.COMPLETED
            config["training_completed_at"] = datetime.now().isoformat()
            config["actual_training_duration"] = (
                actual_training_duration  # Actual time taken
            )
            config["model_metrics"] = model.get_metrics()

            # Cache model in memory
            self.loaded_models[model_id] = model

            # Save config to file
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            loguru.logger.info(
                f"Model {model_id} trained successfully in {actual_training_duration:.2f}s"
            )

            return ModelTrainingResult(
                model_id=model_id,
                status="success",
                training_time=actual_training_duration,
                metrics=model.get_metrics(),
            )

        except (FileNotFoundError, ValueError, KeyError) as e:
            # Update status to failed
            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = ModelStatus.FAILED
                self.model_configs[model_id]["error"] = str(e)

            loguru.logger.error(f"Error training model {model_id}: {str(e)}")
            return ModelTrainingResult(
                model_id=model_id,
                status="error",
                training_time=0.0,
                metrics={},
            )

    def load_model(self, model_id: str) -> BaseRecommender:
        """Load a trained model from disk."""
        try:
            # Check if the model is already loaded in memory
            if model_id in self.loaded_models:
                return self.loaded_models[model_id]

            # Load config
            config_path = self.models_dir / f"{model_id}_config.json"
            if not config_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found for model {model_id}"
                )

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Check if a model file exists
            model_path = config["model_path"]
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")

            # Load model
            model_class = self.get_model_class(config["algorithm"])
            model = model_class.load(model_path)

            # Cache in memory
            self.loaded_models[model_id] = model
            self.model_configs[model_id] = config

            loguru.logger.info(f"Loaded model {model_id}")
            return model

        except (FileNotFoundError, ValueError) as e:
            loguru.logger.error(f"Error loading model {model_id}: {str(e)}")
            raise

    def predict_recommendations(
            self, model_id: str, user_id: str, top_k: int = 10
    ) -> ModelPredictResult:
        """Generate recommendations for a single user."""
        try:
            # Load model if not in memory
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Generate predictions for single user
            predictions_df = model.predict([user_id], n_recommendations=top_k)

            # Convert to desired output format
            user_predictions = predictions_df[predictions_df["user_id"] == user_id]
            predictions = {
                user_id: [
                    {"item_id": row["item_id"], "score": float(row["score"])}
                    for _, row in user_predictions.iterrows()
                ]
            }

            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions=predictions,
                datetime=datetime.now().isoformat(),
                status=ModelStatus.COMPLETED,
            )
        except (FileNotFoundError, ValueError, KeyError) as e:
            loguru.logger.error(f"Error predicting with model {model_id}: {str(e)}")
            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions={},
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def predict_recommendations_batch(
            self, model_id: str, user_ids: List[str], top_k: int = 10
    ) -> List[ModelPredictResult]:
        """Generate recommendations for multiple users."""
        results = []
        for user_id in user_ids:
            result = self.predict_recommendations(model_id, user_id, top_k)
            results.append(result)
        return results

    def predict_scores(
            self,
            model_id: str,
            user_ids: List[str],
            item_ids: List[str],
    ) -> ModelPredictScoresResult:
        """Predict scores for specific user-item pairs."""
        try:
            # Load model if not in memory
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Ensure equal length arrays
            if len(user_ids) == 1 and len(item_ids) > 1:
                user_ids = user_ids * len(item_ids)
            elif len(item_ids) == 1 and len(user_ids) > 1:
                item_ids = item_ids * len(user_ids)
            elif len(user_ids) != len(item_ids):
                raise ValueError("user_ids and item_ids must have the same length")

            # Predict scores
            scores = model.predict_score(user_ids, item_ids)

            # Format results
            results = [
                {"user_id": user_id, "item_id": item_id, "score": float(score)}
                for user_id, item_id, score in zip(user_ids, item_ids, scores)
            ]

            return ModelPredictScoresResult(
                model_id=model_id,
                results=results,
                datetime=datetime.now().isoformat(),
                status=ModelStatus.COMPLETED,
            )
        except (FileNotFoundError, ValueError, KeyError) as e:
            loguru.logger.error(
                f"Error predicting scores with model {model_id}: {str(e)}"
            )
            return ModelPredictScoresResult(
                model_id=model_id,
                results=[],
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def evaluate_model(
            self,
            model_id: str,
            test_data: pd.DataFrame,
            k_values: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model using test data.

        Args:
            model_id: Model identifier
            test_data: Test data DataFrame
            k_values: K values for evaluation metrics (default: [5, 10, 20])

        Returns:
            Evaluation results dictionary
        """
        if k_values is None:
            k_values = [5, 10, 20]

        try:
            # Load model
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Generate predictions for test users
            test_users = test_data["user_id"].unique().tolist()
            predictions_df = model.predict(test_users, n_recommendations=max(k_values))

            # Evaluate using ranking metrics
            ranking_metrics = RecommenderEvaluator.evaluate_recommendations(
                predictions_df, test_data, k_values
            )

            # Calculate coverage metrics
            all_items = set(test_data["item_id"].unique())
            coverage_metrics = RecommenderEvaluator.coverage_metrics(
                predictions_df, all_items
            )

            # Combine results
            evaluation_results = {
                "model_id": model_id,
                "ranking_metrics": ranking_metrics,
                "coverage_metrics": coverage_metrics,
                "evaluation_timestamp": datetime.now().isoformat(),
                "test_users": len(test_users),
                "total_predictions": len(predictions_df),
                "k_values": k_values,
            }

            loguru.logger.info(
                f"Evaluated model {model_id} on test data with {len(test_users)} users"
            )
            return evaluation_results

        except (FileNotFoundError, ValueError, KeyError) as e:
            loguru.logger.error(f"Error evaluating model {model_id}: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        models = []

        # Check for config files in models directory
        for config_file in self.models_dir.glob("*_config.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                model_info = {
                    "model_id": config["model_id"],
                    "model_name": config.get("model_name", ""),
                    "algorithm": config["algorithm"],
                    "status": config["status"],
                    "created_at": config.get("created_at"),
                    "training_time": config.get("training_time"),  # Retrain interval
                    "actual_training_duration": config.get(
                        "actual_training_duration"
                    ),  # Actual time taken
                    "metrics": config.get("model_metrics", {}),
                }

                models.append(model_info)

            except (json.JSONDecodeError, OSError) as e:
                loguru.logger.warning(f"Error reading config {config_file}: {str(e)}")
        return models

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a model."""
        try:
            config_path = self.models_dir / f"{model_id}_config.json"
            if not config_path.exists():
                raise FileNotFoundError(f"Model {model_id} not found")

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Check if a model file exists
            model_exists = os.path.exists(config["model_path"])

            # Get model in memory status
            in_memory = model_id in self.loaded_models

            model_info = {
                **config,
                "model_file_exists": model_exists,
                "loaded_in_memory": in_memory,
                "file_size_mb": 0.0,
            }

            # Get file size if exists
            if model_exists:
                file_size = os.path.getsize(config["model_path"])
                model_info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            return model_info

        except Exception as e:
            loguru.logger.error(f"Error getting model info {model_id}: {str(e)}")
            raise

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        """Delete a model and its associated files."""
        try:
            # Remove from memory cache
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]

            if model_id in self.model_configs:
                del self.model_configs[model_id]

            # Delete files
            files_deleted = []

            # Delete model file
            model_path = self.models_dir / f"{model_id}.pkl"
            if model_path.exists():
                model_path.unlink()
                files_deleted.append(str(model_path))

            # Delete config file
            config_path = self.models_dir / f"{model_id}_config.json"
            if config_path.exists():
                config_path.unlink()
                files_deleted.append(str(config_path))

            loguru.logger.info(f"Deleted model {model_id}")
            return {
                "model_id": model_id,
                "status": "deleted",
                "files_deleted": files_deleted,
            }

        except (FileNotFoundError, ValueError, KeyError) as e:
            loguru.logger.error(f"Error deleting model {model_id}: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def should_retrain_model(self, model_id: str) -> bool:
        """
        Check if a model should be retrained based on its training_time interval.

        Args:
            model_id: Model identifier

        Returns:
            True if model should be retrained, False otherwise
        """
        try:
            model_info = self.get_model_info(model_id)

            # If no training_time is set, no automatic retraining
            if not model_info.get("training_time"):
                return False

            # If no training_completed_at, model was never trained
            if not model_info.get("training_completed_at"):
                return True

            # Calculate time since last training
            last_training = datetime.fromisoformat(model_info["training_completed_at"])
            time_since_training = (datetime.now() - last_training).total_seconds()

            # Check if an interval has passed
            return time_since_training >= model_info["training_time"]

        except (FileNotFoundError, ValueError, KeyError) as e:
            loguru.logger.error(
                f"Error checking retrain status for model {model_id}: {str(e)}"
            )
            return False

    def get_available_algorithms(self) -> List[str]:
        """Get a list of available algorithms."""
        return list(self.model_registry.keys())

    def clear_memory_cache(self) -> int:
        """Clear all models from memory cache."""
        count = len(self.loaded_models)
        self.loaded_models.clear()
        loguru.logger.info(f"Cleared {count} models from memory cache")
        return count
