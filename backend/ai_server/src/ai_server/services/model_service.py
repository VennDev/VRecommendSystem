import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import loguru
import pandas as pd

# Import models from the models folder
from ai_server.models import BaseRecommendationModel, ModelRegistry

# Schemas
from ai_server.schemas.model_schemas import (
    ModelTrainingResult,
    ModelPredictResult,
    ModelPredictScoresResult,
    ModelStatus,
)

SAMPLE_INTERACTION_DATA = pd.DataFrame(
    {
        "user_id": ["u1", "u1", "u2", "u2"],
        "item_id": ["i1", "i2", "i1", "i3"],
        "rating": [5, 4, 3, 5],
    }
)


class ModelService:
    """
    Enhanced Model Service supporting multiple recommendation model types
    Uses the BaseRecommendationModel architecture and ModelRegistry
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # In-memory model cache - now supports any BaseRecommendationModel
        self.loaded_models: Dict[str, BaseRecommendationModel] = {}

        # Model configuration storage
        self.model_configs: Dict[str, Dict[str, Any]] = {}

        # Training state for incremental learning
        self.training_states: Dict[str, Dict[str, Any]] = {}

        # Supported algorithms mapped to model types and their default parameters
        self.supported_algorithms = {
            # LightFM algorithms
            "lightfm_warp": {"model_type": "lightfm", "loss": "warp"},
            "lightfm_bpr": {"model_type": "lightfm", "loss": "bpr"},
            "lightfm_logistic": {"model_type": "lightfm", "loss": "logistic"},
            "lightfm_warp_kos": {"model_type": "lightfm", "loss": "warp-kos"},
            # Legacy support (maps to LightFM)
            "warp": {"model_type": "lightfm", "loss": "warp"},
            "bpr": {"model_type": "lightfm", "loss": "bpr"},
            "logistic": {"model_type": "lightfm", "loss": "logistic"},
            "warp-kos": {"model_type": "lightfm", "loss": "warp-kos"},
        }

    def get_available_algorithms(self) -> List[str]:
        """Get available algorithms"""
        return list(self.supported_algorithms.keys())

    def get_available_model_types(self) -> List[str]:
        """Get available model types from registry"""
        return ModelRegistry.list_models()

    def get_model_info_by_type(self, model_type: str) -> Dict[str, Any]:
        """Get information about a specific model type"""
        try:
            model_class = ModelRegistry.get_model(model_type)
            return {
                "model_type": model_type,
                "class_name": model_class.__name__,
                "description": model_class.__doc__ or "No description available",
                "module": model_class.__module__,
            }
        except ValueError as e:
            return {"error": str(e)}

    def _clean_and_validate_data(
        self, data: pd.DataFrame, data_type: str = "interaction"
    ) -> pd.DataFrame:
        """Clean and validate input data"""
        if data.empty:
            raise ValueError(f"Empty {data_type} data provided")

        cleaned_data = data.copy()

        if data_type == "interaction":
            required_columns = ["user_id", "item_id"]
            missing_cols = [
                col for col in required_columns if col not in cleaned_data.columns
            ]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Ensure string IDs
            cleaned_data["user_id"] = cleaned_data["user_id"].astype(str)
            cleaned_data["item_id"] = cleaned_data["item_id"].astype(str)

            # Handle ratings
            if "rating" in cleaned_data.columns:
                cleaned_data["rating"] = pd.to_numeric(
                    cleaned_data["rating"], errors="coerce"
                ).fillna(1.0)
            else:
                cleaned_data["rating"] = 1.0

        elif data_type in ["user", "item"]:
            id_column = f"{data_type}_id"
            if id_column not in cleaned_data.columns:
                raise ValueError(f"Missing required column: {id_column}")
            cleaned_data[id_column] = cleaned_data[id_column].astype(str)

        # Remove rows with NaN in critical columns
        critical_columns = (
            ["user_id", "item_id"]
            if data_type == "interaction"
            else [f"{data_type}_id"]
        )
        cleaned_data = cleaned_data.dropna(subset=critical_columns)

        return cleaned_data.drop_duplicates().reset_index(drop=True)

    def initialize_training(
        self,
        model_id: str,
        model_name: str,
        algorithm: str,
        message: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        model_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initialize training session"""
        try:
            if algorithm not in self.supported_algorithms:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Get algorithm configuration
            algo_config = self.supported_algorithms[algorithm].copy()

            # Determine model type
            if model_type is None:
                model_type = algo_config.get("model_type", "lightfm")

            # Merge algorithm defaults with custom hyperparameters
            model_params = {k: v for k, v in algo_config.items() if k != "model_type"}
            if hyperparameters:
                model_params.update(hyperparameters)

            # Create model configuration
            config = {
                "model_id": model_id,
                "model_name": model_name,
                "message": message,
                "algorithm": algorithm,
                "model_type": model_type,
                "hyperparameters": model_params,
                "created_at": datetime.now().isoformat(),
                "status": ModelStatus.TRAINING,
                "model_path": str(self.models_dir / f"{model_id}.pkl"),
            }

            # Store config
            self.model_configs[model_id] = config

            # Initialize model using ModelRegistry
            model = ModelRegistry.create_model(
                model_type, model_id=model_id, **model_params
            )
            self.loaded_models[model_id] = model

            # Initialize training state
            self.training_states[model_id] = {
                "total_batches": 0,
                "total_interactions": 0,
                "accumulated_data": [],
                "user_features": None,
                "item_features": None,
            }

            loguru.logger.info(
                f"Training initialized for model {model_id} (type: {model_type})"
            )

            return {
                "model_id": model_id,
                "status": "initialized",
                "message": f"Training session ready for incremental data (model type: {model_type})",
            }

        except ValueError as e:
            loguru.logger.error(f"Error initializing training: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}
        except Exception as e:
            loguru.logger.exception(f"Unexpected error initializing training: {str(e)}")
            raise

    def train_batch(
        self,
        model_id: str,
        interaction_data: pd.DataFrame,
        user_features: Optional[pd.DataFrame] = None,
        item_features: Optional[pd.DataFrame] = None,
        accumulate_data: bool = True,
    ) -> Dict[str, Any]:
        """Train a batch of data"""
        try:
            if model_id not in self.loaded_models:
                raise ValueError(f"Model {model_id} not initialized")

            # Clean data
            cleaned_data = self._clean_and_validate_data(
                interaction_data, "interaction"
            )

            training_state = self.training_states[model_id]

            # Store features (first time or update)
            if user_features is not None:
                cleaned_user_features = self._clean_and_validate_data(
                    user_features, "user"
                )
                if training_state["user_features"] is None:
                    training_state["user_features"] = cleaned_user_features
                else:
                    # Merge with existing features
                    training_state["user_features"] = (
                        pd.concat(
                            [training_state["user_features"], cleaned_user_features]
                        )
                        .drop_duplicates(subset=["user_id"])
                        .reset_index(drop=True)
                    )

            if item_features is not None:
                cleaned_item_features = self._clean_and_validate_data(
                    item_features, "item"
                )
                if training_state["item_features"] is None:
                    training_state["item_features"] = cleaned_item_features
                else:
                    training_state["item_features"] = (
                        pd.concat(
                            [training_state["item_features"], cleaned_item_features]
                        )
                        .drop_duplicates(subset=["item_id"])
                        .reset_index(drop=True)
                    )

            # Accumulate data
            if accumulate_data:
                training_state["accumulated_data"].append(cleaned_data)

            # Update counters
            training_state["total_batches"] += 1
            training_state["total_interactions"] += len(cleaned_data)

            loguru.logger.info(
                f"Batch {training_state['total_batches']} processed for {model_id}"
            )

            return {
                "model_id": model_id,
                "status": "batch_processed",
                "total_batches": training_state["total_batches"],
                "total_interactions": training_state["total_interactions"],
                "batch_size": len(cleaned_data),
            }

        except Exception as e:
            loguru.logger.error(f"Error processing batch: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def finalize_training(self, model_id: str) -> ModelTrainingResult:
        """Finalize training with all accumulated data"""
        try:
            if (
                model_id not in self.loaded_models
                or model_id not in self.training_states
            ):
                raise ValueError(f"Model {model_id} not in training state")

            training_state = self.training_states[model_id]
            model = self.loaded_models[model_id]
            config = self.model_configs[model_id]

            if not training_state["accumulated_data"]:
                raise ValueError("No training data accumulated")

            # Combine all data
            combined_data = pd.concat(
                training_state["accumulated_data"], ignore_index=True
            )
            combined_data = self._clean_and_validate_data(combined_data, "interaction")

            loguru.logger.info(
                f"Training {model_id} with {len(combined_data)} interactions"
            )

            # Train model
            model.fit(
                combined_data,
                training_state["user_features"],
                training_state["item_features"],
                epochs=config["hyperparameters"].get("epochs", 10),
            )

            # Update config
            config["status"] = ModelStatus.COMPLETED
            config["training_completed_at"] = datetime.now().isoformat()
            config["model_metrics"] = model.metrics

            # Clean up training state
            del self.training_states[model_id]

            loguru.logger.info(f"Training completed for {model_id}")

            return ModelTrainingResult(
                model_id=model_id, status="success", metrics=model.metrics
            )

        except Exception as e:
            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = ModelStatus.FAILED
                self.model_configs[model_id]["error"] = str(e)

            if model_id in self.training_states:
                del self.training_states[model_id]

            loguru.logger.error(f"Training failed: {str(e)}")
            return ModelTrainingResult(model_id=model_id, status="error", metrics={})

    def save_model(self, model_id: str) -> Dict[str, Any]:
        """Save trained model"""
        try:
            if model_id not in self.loaded_models:
                raise ValueError(f"Model {model_id} not found")

            model = self.loaded_models[model_id]
            config = self.model_configs[model_id]

            if not model.is_fitted:
                raise ValueError(f"Model {model_id} not trained")

            # Save model
            model_path = config["model_path"]
            model.save(model_path)

            # Save config
            config["last_saved_at"] = datetime.now().isoformat()
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2, default=str)

            file_size_mb = os.path.getsize(model_path) / (1024 * 1024)

            loguru.logger.info(f"Model {model_id} saved ({file_size_mb:.2f} MB)")

            return {
                "model_id": model_id,
                "status": "saved",
                "model_path": model_path,
                "file_size_mb": round(file_size_mb, 2),
            }

        except Exception as e:
            loguru.logger.error(f"Error saving model: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def load_model(self, model_id: str) -> BaseRecommendationModel:
        """Load model from disk"""
        try:
            if model_id in self.loaded_models:
                return self.loaded_models[model_id]

            # Load config
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "r") as f:
                config = json.load(f)

            # Get model type from config
            model_type = config.get(
                "model_type", "lightfm"
            )  # Default to lightfm for backward compatibility

            # Load model using the appropriate class
            model_path = config["model_path"]
            model_class = ModelRegistry.get_model(model_type)
            model = model_class.load(model_path)

            # Cache in memory
            self.loaded_models[model_id] = model
            self.model_configs[model_id] = config

            loguru.logger.info(f"Loaded model {model_id} (type: {model_type})")
            return model

        except Exception as e:
            loguru.logger.error(f"Error loading model: {str(e)}")
            raise

    def predict_recommendations(
        self, model_id: str, user_id: str, top_k: int = 10
    ) -> ModelPredictResult:
        """Generate recommendations for a user"""
        try:
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]
            predictions_df = model.predict([user_id], n_recommendations=top_k)

            predictions = {
                user_id: [
                    {"item_id": row["item_id"], "score": float(row["score"])}
                    for _, row in predictions_df.iterrows()
                    if row["user_id"] == user_id
                ]
            }

            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions=predictions,
                datetime=datetime.now().isoformat(),
                status=ModelStatus.COMPLETED,
            )

        except Exception as e:
            loguru.logger.error(f"Prediction error: {str(e)}")
            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions={},
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def predict_scores(
        self, model_id: str, user_ids: List[str], item_ids: List[str]
    ) -> ModelPredictScoresResult:
        """Predict scores for user-item pairs"""
        try:
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Handle different input lengths
            if len(user_ids) == 1 and len(item_ids) > 1:
                user_ids = user_ids * len(item_ids)
            elif len(item_ids) == 1 and len(user_ids) > 1:
                item_ids = item_ids * len(user_ids)

            scores = model.predict_score(user_ids, item_ids)

            results = [
                {"user_id": user_id, "item_id": item_id, "score": score}
                for user_id, item_id, score in zip(user_ids, item_ids, scores)
            ]

            return ModelPredictScoresResult(
                model_id=model_id,
                results=results,
                datetime=datetime.now().isoformat(),
                status=ModelStatus.COMPLETED,
            )

        except Exception as e:
            loguru.logger.error(f"Score prediction error: {str(e)}")
            return ModelPredictScoresResult(
                model_id=model_id,
                results=[],
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def evaluate_model(
        self, model_id: str, test_data: pd.DataFrame, k_values: List[int] = [5, 10, 20]
    ) -> Dict[str, Any]:
        """Evaluate model performance"""
        try:
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]
            cleaned_test_data = self._clean_and_validate_data(test_data, "interaction")

            metrics = model.evaluate(cleaned_test_data, k_values)

            return {
                "model_id": model_id,
                "metrics": metrics,
                "evaluation_timestamp": datetime.now().isoformat(),
                "test_interactions": len(cleaned_test_data),
            }

        except Exception as e:
            loguru.logger.error(f"Evaluation error: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    # Keep other methods from original service for compatibility
    def list_models(self) -> List[Dict[str, Any]]:
        """List all models"""
        models = []
        for config_file in self.models_dir.glob("*_config.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                models.append(config)
            except Exception as e:
                loguru.logger.warning(f"Error reading {config_file}: {e}")
        return models

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information"""
        try:
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "r") as f:
                config = json.load(f)

            model_exists = os.path.exists(config["model_path"])
            in_memory = model_id in self.loaded_models
            in_training = model_id in self.training_states

            info = {
                **config,
                "model_file_exists": model_exists,
                "loaded_in_memory": in_memory,
                "in_training_state": in_training,
                "file_size_mb": 0.0,
            }

            if model_exists:
                file_size = os.path.getsize(config["model_path"])
                info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            return info

        except Exception as e:
            loguru.logger.error(f"Error getting model info: {str(e)}")
            raise

    def delete_model(self, model_id: str) -> Dict[str, Any]:
        """Delete model and files"""
        try:
            # Cancel training if in progress
            if model_id in self.training_states:
                del self.training_states[model_id]

            # Remove from memory
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]

            if model_id in self.model_configs:
                del self.model_configs[model_id]

            # Delete files
            files_deleted = []

            model_path = self.models_dir / f"{model_id}.pkl"
            if model_path.exists():
                model_path.unlink()
                files_deleted.append(str(model_path))

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

        except Exception as e:
            loguru.logger.error(f"Error deleting model: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def get_training_status(self, model_id: str) -> Dict[str, Any]:
        """Get training status"""
        try:
            if model_id not in self.model_configs:
                return {
                    "model_id": model_id,
                    "status": "not_found",
                    "message": "Model not found",
                }

            config = self.model_configs[model_id]

            if model_id in self.training_states:
                training_state = self.training_states[model_id]
                return {
                    "model_id": model_id,
                    "status": "training_in_progress",
                    "total_batches": training_state["total_batches"],
                    "total_interactions": training_state["total_interactions"],
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
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def cancel_training(self, model_id: str) -> Dict[str, Any]:
        """Cancel training"""
        try:
            if model_id not in self.training_states:
                return {
                    "model_id": model_id,
                    "status": "not_training",
                    "message": "Model not in training state",
                }

            training_state = self.training_states[model_id]
            total_batches = training_state["total_batches"]
            total_interactions = training_state["total_interactions"]

            del self.training_states[model_id]

            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = ModelStatus.FAILED
                self.model_configs[model_id][
                    "cancelled_at"
                ] = datetime.now().isoformat()

            if model_id in self.loaded_models:
                del self.loaded_models[model_id]

            return {
                "model_id": model_id,
                "status": "cancelled",
                "batches_processed": total_batches,
                "interactions_processed": total_interactions,
            }

        except Exception as e:
            return {"model_id": model_id, "status": "error", "error": str(e)}

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
        """Direct training method for backward compatibility"""
        try:
            # Initialize training
            init_result = self.initialize_training(
                model_id, model_name, algorithm, message, hyperparameters
            )
            if init_result["status"] != "initialized":
                raise ValueError(f"Failed to initialize: {init_result}")

            # Process single batch
            batch_result = self.train_batch(
                model_id, interaction_data, user_features, item_features
            )
            if batch_result["status"] != "batch_processed":
                raise ValueError(f"Failed to process batch: {batch_result}")

            # Finalize training
            training_result = self.finalize_training(model_id)
            if training_result.status != "success":
                raise ValueError(f"Training failed: {training_result}")

            # Save model
            save_result = self.save_model(model_id)
            if save_result["status"] != "saved":
                loguru.logger.warning(f"Model trained but not saved: {save_result}")

            return training_result

        except Exception as e:
            loguru.logger.error(f"Direct training error: {str(e)}")
            return ModelTrainingResult(model_id=model_id, status="error", metrics={})

    def predict_recommendations_batch(
        self, model_id: str, user_ids: List[str], top_k: int = 10
    ) -> List[ModelPredictResult]:
        """Batch predictions"""
        results = []
        for user_id in user_ids:
            result = self.predict_recommendations(model_id, user_id, top_k)
            results.append(result)
        return results

    def clear_memory_cache(self) -> int:
        """Clear memory cache"""
        count = len(self.loaded_models)
        self.loaded_models.clear()
        loguru.logger.info(f"Cleared {count} models from memory")
        return count

    def get_memory_usage_info(self) -> Dict[str, Any]:
        """Get memory usage info"""
        return {
            "loaded_models_count": len(self.loaded_models),
            "training_sessions_count": len(self.training_states),
            "loaded_model_ids": list(self.loaded_models.keys()),
            "training_model_ids": list(self.training_states.keys()),
        }
