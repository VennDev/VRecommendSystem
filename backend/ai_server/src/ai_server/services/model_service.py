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
    Enhanced service class for managing recommendation models with incremental training support.
    Handles training, loading, saving, and prediction operations using DataFrames with streaming capability.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # In-memory model cache
        self.loaded_models: Dict[str, BaseRecommender] = {}

        # Model configuration storage
        self.model_configs: Dict[str, Dict[str, Any]] = {}

        # Training state for incremental learning
        self.training_states: Dict[str, Dict[str, Any]] = {}

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

    def initialize_training(
            self,
            model_id: str,
            model_name: str,
            algorithm: str,
            message: str,
            hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a training session for incremental learning.

        Args:
            model_id: Unique identifier for the model
            model_name: User-friendly name for the model
            algorithm: Algorithm name (als, bpr, ncf, tfidf, feature)
            hyperparameters: Model hyperparameters
            message: Description or message about the model

        Returns:
            Dictionary with initialization status
        """
        try:
            loguru.logger.info(
                f"Initializing training session for model {model_id} with algorithm {algorithm}"
            )

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
            }

            # Store config
            self.model_configs[model_id] = config

            # Initialize model
            model_class = self.get_model_class(algorithm)
            model = model_class(**config["hyperparameters"])

            # Cache model in memory for incremental training
            self.loaded_models[model_id] = model

            # Initialize training state
            self.training_states[model_id] = {
                "is_initialized": False,
                "total_batches": 0,
                "total_interactions": 0,
                "last_batch_time": None,
                "accumulated_data": [],
                "user_features": None,
                "item_features": None,
                "encoders_fitted": False,
            }

            loguru.logger.info(f"Training session initialized for model {model_id}")

            return {
                "model_id": model_id,
                "status": "initialized",
                "message": "Training session ready for incremental data",
            }

        except Exception as e:
            loguru.logger.error(f"Error initializing training for model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "status": "error",
                "error": str(e),
            }

    def train_batch(
            self,
            model_id: str,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            accumulate_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Train a batch of data incrementally.

        Args:
            model_id: Model identifier
            interaction_data: Batch of interaction data
            user_features: Optional user features
            item_features: Optional item features
            accumulate_data: Whether to accumulate data for full training later

        Returns:
            Dictionary with training batch status
        """
        try:
            if model_id not in self.loaded_models:
                raise ValueError(f"Model {model_id} not initialized. Call initialize_training first.")

            if model_id not in self.training_states:
                raise ValueError(f"Training state not found for model {model_id}")

            # Validate interaction data
            DataPreprocessor.validate_data_format(interaction_data)

            training_state = self.training_states[model_id]
            model = self.loaded_models[model_id]

            loguru.logger.info(
                f"Processing batch {training_state['total_batches'] + 1} for model {model_id} "
                f"with {len(interaction_data)} interactions"
            )

            # Store features if provided (first time)
            if user_features is not None and training_state["user_features"] is None:
                training_state["user_features"] = user_features.copy()
            elif user_features is not None:
                # Append new user features
                existing_users = set(training_state["user_features"]["user_id"])
                new_users = user_features[~user_features["user_id"].isin(existing_users)]
                if len(new_users) > 0:
                    training_state["user_features"] = pd.concat([
                        training_state["user_features"],
                        new_users
                    ], ignore_index=True)

            if item_features is not None and training_state["item_features"] is None:
                training_state["item_features"] = item_features.copy()
            elif item_features is not None:
                # Append new item features
                existing_items = set(training_state["item_features"]["item_id"])
                new_items = item_features[~item_features["item_id"].isin(existing_items)]
                if len(new_items) > 0:
                    training_state["item_features"] = pd.concat([
                        training_state["item_features"],
                        new_items
                    ], ignore_index=True)

            # Accumulate data if requested
            if accumulate_data:
                training_state["accumulated_data"].append(interaction_data.copy())

            # Update training state
            training_state["total_batches"] += 1
            training_state["total_interactions"] += len(interaction_data)
            training_state["last_batch_time"] = datetime.now().isoformat()

            # For algorithms that support true online learning (like some neural models),
            # we could train on this batch immediately. For now, we'll accumulate data.

            # Update model config
            self.model_configs[model_id]["last_updated"] = datetime.now().isoformat()

            loguru.logger.info(
                f"Batch processed for model {model_id}. "
                f"Total batches: {training_state['total_batches']}, "
                f"Total interactions: {training_state['total_interactions']}"
            )

            return {
                "model_id": model_id,
                "status": "batch_processed",
                "total_batches": training_state["total_batches"],
                "total_interactions": training_state["total_interactions"],
                "batch_size": len(interaction_data),
            }

        except Exception as e:
            loguru.logger.error(f"Error processing batch for model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "status": "error",
                "error": str(e),
            }

    def finalize_training(self, model_id: str) -> ModelTrainingResult:
        """
        Finalize training using all accumulated data.

        Args:
            model_id: Model identifier

        Returns:
            ModelTrainingResult with training completion status
        """
        try:
            if model_id not in self.loaded_models or model_id not in self.training_states:
                raise ValueError(f"Model {model_id} not in training state")

            training_state = self.training_states[model_id]
            model = self.loaded_models[model_id]
            config = self.model_configs[model_id]

            if not training_state["accumulated_data"]:
                raise ValueError(f"No training data accumulated for model {model_id}")

            loguru.logger.info(
                f"Finalizing training for model {model_id} with "
                f"{training_state['total_batches']} batches and "
                f"{training_state['total_interactions']} total interactions"
            )

            # Combine all accumulated data
            combined_interaction_data = pd.concat(
                training_state["accumulated_data"],
                ignore_index=True
            ).drop_duplicates()

            loguru.logger.info(
                f"Combined data shape: {combined_interaction_data.shape} "
                f"(after removing duplicates)"
            )

            # Train the model on all accumulated data
            start_time = datetime.now()
            model.fit(
                combined_interaction_data,
                training_state["user_features"],
                training_state["item_features"]
            )
            training_duration = (datetime.now() - start_time).total_seconds()

            # Update configuration
            config["status"] = ModelStatus.COMPLETED
            config["training_completed_at"] = datetime.now().isoformat()
            config["training_duration_seconds"] = training_duration
            config["model_metrics"] = model.get_metrics()
            config["total_batches"] = training_state["total_batches"]
            config["total_interactions"] = training_state["total_interactions"]

            # Clean up training state
            del self.training_states[model_id]

            loguru.logger.info(
                f"Training completed for model {model_id} in {training_duration:.2f} seconds"
            )

            return ModelTrainingResult(
                model_id=model_id,
                status="success",
                metrics=model.get_metrics(),
            )

        except Exception as e:
            # Update status to failed
            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = ModelStatus.FAILED
                self.model_configs[model_id]["error"] = str(e)

            # Clean up training state
            if model_id in self.training_states:
                del self.training_states[model_id]

            loguru.logger.error(f"Error finalizing training for model {model_id}: {str(e)}")
            return ModelTrainingResult(
                model_id=model_id,
                status="error",
                metrics={},
            )

    def save_model(self, model_id: str) -> Dict[str, Any]:
        """
        Save a trained model to disk.

        Args:
            model_id: Model identifier

        Returns:
            Dictionary with save status
        """
        try:
            if model_id not in self.loaded_models:
                raise ValueError(f"Model {model_id} not found in memory")

            model = self.loaded_models[model_id]
            config = self.model_configs[model_id]

            if not model.is_fitted:
                raise ValueError(f"Model {model_id} is not trained yet")

            # Save model
            model_path = config["model_path"]
            model.save(model_path)

            # Save config
            config["last_saved_at"] = datetime.now().isoformat()
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            # Get file size
            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)

            loguru.logger.info(f"Model {model_id} saved successfully ({file_size_mb:.2f} MB)")

            return {
                "model_id": model_id,
                "status": "saved",
                "model_path": model_path,
                "config_path": str(config_path),
                "file_size_mb": round(file_size_mb, 2),
            }

        except Exception as e:
            loguru.logger.error(f"Error saving model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "status": "error",
                "error": str(e),
            }

    def get_training_status(self, model_id: str) -> Dict[str, Any]:
        """
        Get current training status for a model.

        Args:
            model_id: Model identifier

        Returns:
            Dictionary with training status information
        """
        try:
            if model_id not in self.model_configs:
                return {
                    "model_id": model_id,
                    "status": "not_found",
                    "message": "Model not found"
                }

            config = self.model_configs[model_id]

            # Check if in training state
            if model_id in self.training_states:
                training_state = self.training_states[model_id]
                return {
                    "model_id": model_id,
                    "status": "training_in_progress",
                    "total_batches": training_state["total_batches"],
                    "total_interactions": training_state["total_interactions"],
                    "last_batch_time": training_state["last_batch_time"],
                    "has_user_features": training_state["user_features"] is not None,
                    "has_item_features": training_state["item_features"] is not None,
                    "config": config,
                }
            else:
                return {
                    "model_id": model_id,
                    "status": config.get("status", "unknown"),
                    "config": config,
                    "in_memory": model_id in self.loaded_models,
                }

        except Exception as e:
            loguru.logger.error(f"Error getting training status for model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "status": "error",
                "error": str(e),
            }

    def cancel_training(self, model_id: str) -> Dict[str, Any]:
        """
        Cancel ongoing training for a model.

        Args:
            model_id: Model identifier

        Returns:
            Dictionary with cancellation status
        """
        try:
            if model_id not in self.training_states:
                return {
                    "model_id": model_id,
                    "status": "not_training",
                    "message": "Model is not currently in training state"
                }

            # Clean up training state
            training_state = self.training_states[model_id]
            total_batches = training_state["total_batches"]
            total_interactions = training_state["total_interactions"]

            del self.training_states[model_id]

            # Update config status
            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = ModelStatus.FAILED
                self.model_configs[model_id]["cancelled_at"] = datetime.now().isoformat()
                self.model_configs[model_id]["cancellation_reason"] = "Manual cancellation"

            # Remove from memory
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]

            loguru.logger.info(f"Training cancelled for model {model_id}")

            return {
                "model_id": model_id,
                "status": "cancelled",
                "batches_processed": total_batches,
                "interactions_processed": total_interactions,
            }

        except Exception as e:
            loguru.logger.error(f"Error cancelling training for model {model_id}: {str(e)}")
            return {
                "model_id": model_id,
                "status": "error",
                "error": str(e),
            }

    # Keep all original methods for backward compatibility
    def train_save_model(
            self,
            model_id: str,
            model_name: str,
            algorithm: str,
            message: str,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> ModelTrainingResult:
        """
        Train a model from DataFrames (original method for backward compatibility).
        """
        try:
            loguru.logger.info(
                f"Starting direct training for model {model_id} with algorithm {algorithm}"
            )

            # Initialize training
            init_result = self.initialize_training(
                model_id, model_name, algorithm, message, hyperparameters
            )
            if init_result["status"] != "initialized":
                raise ValueError(f"Failed to initialize training: {init_result}")

            # Process as single batch
            batch_result = self.train_batch(
                model_id, interaction_data, user_features, item_features
            )
            if batch_result["status"] != "batch_processed":
                raise ValueError(f"Failed to process batch: {batch_result}")

            # Finalize training
            training_result = self.finalize_training(model_id)
            if training_result.status != "success":
                raise ValueError(f"Failed to finalize training: {training_result}")

            # Save model
            save_result = self.save_model(model_id)
            if save_result["status"] != "saved":
                loguru.logger.warning(f"Model trained but not saved: {save_result}")

            loguru.logger.info(f"Model {model_id} trained and saved successfully!")

            return training_result

        except Exception as e:
            loguru.logger.error(f"Error in direct training for model {model_id}: {str(e)}")
            return ModelTrainingResult(
                model_id=model_id,
                status="error",
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
        """Evaluate a trained model using test data."""
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
                    "training_time": config.get("training_time"),
                    "actual_training_duration": config.get("training_duration_seconds"),
                    "metrics": config.get("model_metrics", {}),
                    "total_batches": config.get("total_batches", 0),
                    "total_interactions": config.get("total_interactions", 0),
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
            in_training = model_id in self.training_states

            model_info = {
                **config,
                "model_file_exists": model_exists,
                "loaded_in_memory": in_memory,
                "in_training_state": in_training,
                "file_size_mb": 0.0,
            }

            # Get file size if exists
            if model_exists:
                file_size = os.path.getsize(config["model_path"])
                model_info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            # Add training state info if in training
            if in_training:
                training_state = self.training_states[model_id]
                model_info["training_state"] = {
                    "total_batches": training_state["total_batches"],
                    "total_interactions": training_state["total_interactions"],
                    "last_batch_time": training_state["last_batch_time"],
                }

            return model_info

        except Exception as e:
            loguru.logger.error(f"Error getting model info {model_id}: {str(e)}")
            raise

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        """Delete a model and its associated files."""
        try:
            # Cancel training if in progress
            if model_id in self.training_states:
                self.cancel_training(model_id)

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

    def get_available_algorithms(self) -> List[str]:
        """Get a list of available algorithms."""
        return list(self.model_registry.keys())

    def clear_memory_cache(self) -> int:
        """Clear all models from memory cache."""
        count = len(self.loaded_models)
        self.loaded_models.clear()
        loguru.logger.info(f"Cleared {count} models from memory cache")
        return count

    def get_memory_usage_info(self) -> Dict[str, Any]:
        """Get information about memory usage."""
        import sys

        memory_info = {
            "loaded_models_count": len(self.loaded_models),
            "training_sessions_count": len(self.training_states),
            "loaded_model_ids": list(self.loaded_models.keys()),
            "training_model_ids": list(self.training_states.keys()),
        }

        # Get approximate memory usage for each loaded model
        model_memory = {}
        for model_id, model in self.loaded_models.items():
            try:
                # Estimate of model memory usage
                model_size = sys.getsizeof(model)
                if hasattr(model, 'user_factors') and model.user_factors is not None:
                    model_size += model.user_factors.nbytes
                if hasattr(model, 'item_factors') and model.item_factors is not None:
                    model_size += model.item_factors.nbytes

                model_memory[model_id] = round(model_size / (1024 * 1024), 2)  # MB
            except:
                model_memory[model_id] = "unknown"

        memory_info["model_memory_mb"] = model_memory

        return memory_info

    def cleanup_failed_training_sessions(self) -> Dict[str, Any]:
        """Clean up any failed or stale training sessions."""
        cleaned_sessions = []

        for model_id in list(self.training_states.keys()):
            try:
                # Check if session has been inactive for too long (e.g., 24 hours)
                training_state = self.training_states[model_id]
                if training_state.get("last_batch_time"):
                    from datetime import datetime, timedelta
                    last_batch = datetime.fromisoformat(training_state["last_batch_time"])
                    if datetime.now() - last_batch > timedelta(hours=24):
                        self.cancel_training(model_id)
                        cleaned_sessions.append(model_id)
            except Exception as e:
                loguru.logger.warning(f"Error checking training session {model_id}: {str(e)}")

        return {
            "cleaned_sessions": cleaned_sessions,
            "count": len(cleaned_sessions),
        }

    def export_model_metadata(self, model_id: str) -> Dict[str, Any]:
        """Export model metadata for backup or migration."""
        try:
            if model_id not in self.model_configs:
                raise ValueError(f"Model {model_id} not found")

            config = self.model_configs[model_id].copy()

            # Add current status info
            metadata = {
                "config": config,
                "export_timestamp": datetime.now().isoformat(),
                "in_memory": model_id in self.loaded_models,
                "in_training": model_id in self.training_states,
            }

            # Add training state if in training
            if model_id in self.training_states:
                training_state = self.training_states[model_id].copy()
                # Remove large data objects for export
                if "accumulated_data" in training_state:
                    training_state["accumulated_data_batches"] = len(training_state["accumulated_data"])
                    del training_state["accumulated_data"]
                if "user_features" in training_state:
                    training_state["has_user_features"] = training_state["user_features"] is not None
                    del training_state["user_features"]
                if "item_features" in training_state:
                    training_state["has_item_features"] = training_state["item_features"] is not None
                    del training_state["item_features"]

                metadata["training_state"] = training_state

            return metadata

        except Exception as e:
            loguru.logger.error(f"Error exporting metadata for model {model_id}: {str(e)}")
            raise

    def get_training_progress(self, model_id: str) -> Dict[str, Any]:
        """Get detailed training progress information."""
        if model_id not in self.training_states:
            return {
                "model_id": model_id,
                "status": "not_in_training",
                "message": "Model is not currently in training state"
            }

        training_state = self.training_states[model_id]
        config = self.model_configs.get(model_id, {})

        # Calculate training statistics
        progress_info = {
            "model_id": model_id,
            "status": "training_in_progress",
            "algorithm": config.get("algorithm", "unknown"),
            "model_name": config.get("model_name", ""),
            "training_started_at": config.get("training_started_at"),
            "total_batches": training_state["total_batches"],
            "total_interactions": training_state["total_interactions"],
            "last_batch_time": training_state["last_batch_time"],
            "has_user_features": training_state["user_features"] is not None,
            "has_item_features": training_state["item_features"] is not None,
        }

        # Calculate average batch size and processing rate
        if training_state["total_batches"] > 0:
            progress_info["avg_batch_size"] = training_state["total_interactions"] / training_state["total_batches"]

        # Calculate time-based metrics if we have timestamps
        if config.get("training_started_at") and training_state["last_batch_time"]:
            try:
                start_time = datetime.fromisoformat(config["training_started_at"])
                last_batch_time = datetime.fromisoformat(training_state["last_batch_time"])

                duration = (last_batch_time - start_time).total_seconds()
                progress_info["training_duration_seconds"] = duration

                if duration > 0:
                    progress_info["interactions_per_second"] = training_state["total_interactions"] / duration
                    progress_info["batches_per_minute"] = (training_state["total_batches"] / duration) * 60

            except Exception as e:
                loguru.logger.warning(f"Error calculating time metrics: {str(e)}")

        return progress_info
