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
    Supports NMF and SVD models for fast, multithreaded training
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # In-memory model cache - supports any BaseRecommendationModel
        self.loaded_models: Dict[str, BaseRecommendationModel] = {}

        # Model configuration storage
        self.model_configs: Dict[str, Dict[str, Any]] = {}

        # Training state for incremental learning
        self.training_states: Dict[str, Dict[str, Any]] = {}

        # Supported algorithms mapped to model types and their default parameters
        self.supported_algorithms = {
            # NMF algorithms with different configurations
            "nmf": {"model_type": "nmf", "n_components": 2, "solver": "mu"},
            "nmf_fast": {"model_type": "nmf", "n_components": 2, "solver": "cd", "max_iter": 100},
            "nmf_accurate": {"model_type": "nmf", "n_components": 2, "solver": "mu", "max_iter": 500},

            # SVD algorithms with different configurations
            "svd": {"model_type": "svd", "n_components": 2, "algorithm": "randomized"},
            "svd_fast": {"model_type": "svd", "n_components": 2, "algorithm": "randomized", "n_iter": 3},
            "svd_accurate": {"model_type": "svd", "n_components": 2, "algorithm": "arpack"},

            # Hybrid approach (you can add more later)
            "hybrid_nmf": {"model_type": "nmf", "n_components": 2, "solver": "mu", "alpha": 0.1},
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
                "supports_multithreading": True,  # All our models support multithreading
            }
        except ValueError as e:
            return {"error": str(e)}

    def get_algorithm_details(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all supported algorithms"""
        details = {}
        for algorithm, config in self.supported_algorithms.items():
            model_type = config["model_type"]
            details[algorithm] = {
                "algorithm": algorithm,
                "model_type": model_type,
                "default_params": {k: v for k, v in config.items() if k != "model_type"},
                "description": self._get_algorithm_description(algorithm),
                "use_case": self._get_algorithm_use_case(algorithm),
            }
        return details

    def _get_algorithm_description(self, algorithm: str) -> str:
        """Get description for algorithm"""
        descriptions = {
            "nmf": "Non-negative Matrix Factorization with balanced performance",
            "nmf_fast": "Fast NMF with coordinate descent solver, good for quick training",
            "nmf_accurate": "High-accuracy NMF with more components and iterations",
            "svd": "Singular Value Decomposition with randomized algorithm",
            "svd_fast": "Fast SVD with fewer components, good for large datasets",
            "svd_accurate": "High-accuracy SVD using ARPACK solver",
            "hybrid_nmf": "NMF with regularization for better generalization",
        }
        return descriptions.get(algorithm, "No description available")

    def _get_algorithm_use_case(self, algorithm: str) -> str:
        """Get use case recommendation for algorithm"""
        use_cases = {
            "nmf": "General purpose, good balance of speed and accuracy",
            "nmf_fast": "Large datasets, real-time applications",
            "nmf_accurate": "High-quality recommendations, smaller datasets",
            "svd": "General collaborative filtering, handles sparsity well",
            "svd_fast": "Very large datasets, memory-constrained environments",
            "svd_accurate": "High-precision requirements, research applications",
            "hybrid_nmf": "Noisy data, better generalization needed",
        }
        return use_cases.get(algorithm, "General purpose")

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
                raise ValueError(
                    f"Unsupported algorithm: {algorithm}. Available: {list(self.supported_algorithms.keys())}")

            # Get algorithm configuration
            algo_config = self.supported_algorithms[algorithm].copy()

            # Determine model type
            if model_type is None:
                model_type = algo_config.get("model_type", "nmf")  # Default to NMF

            # Validate model type
            if model_type not in self.get_available_model_types():
                raise ValueError(f"Unsupported model type: {model_type}. Available: {self.get_available_model_types()}")

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
                f"Training initialized for model {model_id} (type: {model_type}, algorithm: {algorithm})"
            )

            return {
                "model_id": model_id,
                "status": "initialized",
                "algorithm": algorithm,
                "model_type": model_type,
                "message": f"Training session ready for incremental data (model: {model_type}, algorithm: {algorithm})",
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
                raise ValueError(f"Model {model_id} not initialized. Call initialize_training first.")

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
                f"Batch {training_state['total_batches']} processed for {model_id} "
                f"({len(cleaned_data)} interactions)"
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
                f"Training {model_id} ({config['model_type']}) with {len(combined_data)} interactions"
            )

            # Train model with algorithm-specific parameters
            training_kwargs = {}

            # Add any additional training parameters based on model type
            if config['model_type'] == 'nmf':
                # NMF doesn't use epochs parameter, uses max_iter instead
                pass
            elif config['model_type'] == 'svd':
                # SVD doesn't use epochs either
                pass

            model.fit(
                combined_data,
                training_state["user_features"],
                training_state["item_features"],
                **training_kwargs
            )

            # Update config
            config["status"] = ModelStatus.COMPLETED
            config["training_completed_at"] = datetime.now().isoformat()
            config["model_metrics"] = model.metrics
            config["final_stats"] = {
                "total_interactions": len(combined_data),
                "unique_users": combined_data['user_id'].nunique(),
                "unique_items": combined_data['item_id'].nunique(),
                "has_user_features": training_state["user_features"] is not None,
                "has_item_features": training_state["item_features"] is not None,
            }

            # Clean up training state
            del self.training_states[model_id]

            loguru.logger.info(f"Training completed for {model_id} ({config['model_type']})")

            return ModelTrainingResult(
                model_id=model_id,
                status="success",
                metrics=model.metrics
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
                raise ValueError(f"Model {model_id} not found in memory")

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
                "model_type": config["model_type"],
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
            model_type = config.get("model_type", "nmf")  # Default to NMF

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
            loguru.logger.error(f"Error loading model {model_id}: {str(e)}")
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
            loguru.logger.error(f"Prediction error for model {model_id}: {str(e)}")
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

    def get_similar_items(
            self, model_id: str, item_id: str, n_similar: int = 10
    ) -> Dict[str, Any]:
        """Get similar items"""
        try:
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]
            similar_items = model.get_similar_items(item_id, n_similar)

            return {
                "model_id": model_id,
                "item_id": item_id,
                "similar_items": similar_items,
                "count": len(similar_items),
                "status": "success"
            }

        except Exception as e:
            loguru.logger.error(f"Similar items error: {str(e)}")
            return {
                "model_id": model_id,
                "item_id": item_id,
                "similar_items": [],
                "count": 0,
                "status": "error",
                "error": str(e)
            }

    def get_similar_users(
            self, model_id: str, user_id: str, n_similar: int = 10
    ) -> Dict[str, Any]:
        """Get similar users"""
        try:
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]
            similar_users = model.get_similar_users(user_id, n_similar)

            return {
                "model_id": model_id,
                "user_id": user_id,
                "similar_users": similar_users,
                "count": len(similar_users),
                "status": "success"
            }

        except Exception as e:
            loguru.logger.error(f"Similar users error: {str(e)}")
            return {
                "model_id": model_id,
                "user_id": user_id,
                "similar_users": [],
                "count": 0,
                "status": "error",
                "error": str(e)
            }

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
                "model_type": self.model_configs[model_id]["model_type"],
                "metrics": metrics,
                "evaluation_timestamp": datetime.now().isoformat(),
                "test_interactions": len(cleaned_test_data),
                "test_users": cleaned_test_data['user_id'].nunique(),
                "test_items": cleaned_test_data['item_id'].nunique(),
                "status": "success"
            }

        except Exception as e:
            loguru.logger.error(f"Evaluation error: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    # Model management methods
    def list_models(self) -> List[Dict[str, Any]]:
        """List all models"""
        models = []
        for config_file in self.models_dir.glob("*_config.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                # Add file existence check
                model_file_exists = os.path.exists(config.get("model_path", ""))
                config["model_file_exists"] = model_file_exists
                config["loaded_in_memory"] = config["model_id"] in self.loaded_models

                models.append(config)
            except Exception as e:
                loguru.logger.warning(f"Error reading {config_file}: {e}")
        return models

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed model information"""
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

            # Add model-specific info if loaded
            if in_memory:
                model = self.loaded_models[model_id]
                info["model_details"] = model.get_model_info()

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

            # Check for a metadata file
            metadata_path = self.models_dir / f"{model_id}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
                files_deleted.append(str(metadata_path))

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
                    "algorithm": config.get("algorithm"),
                    "model_type": config.get("model_type"),
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
                    "algorithm": config.get("algorithm"),
                    "model_type": config.get("model_type"),
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
                self.model_configs[model_id]["cancelled_at"] = datetime.now().isoformat()

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
        """Batch predictions for multiple users"""
        results = []
        for user_id in user_ids:
            result = self.predict_recommendations(model_id, user_id, top_k)
            results.append(result)
        return results

    def clear_memory_cache(self) -> int:
        """Clear memory cache of loaded models"""
        count = len(self.loaded_models)
        self.loaded_models.clear()
        loguru.logger.info(f"Cleared {count} models from memory")
        return count

    def get_memory_usage_info(self) -> Dict[str, Any]:
        """Get memory usage information"""
        model_details = {}
        for model_id, model in self.loaded_models.items():
            config = self.model_configs.get(model_id, {})
            model_details[model_id] = {
                "model_type": config.get("model_type", "unknown"),
                "algorithm": config.get("algorithm", "unknown"),
                "is_fitted": model.is_fitted,
                "n_users": len(model.user_id_mapping) if hasattr(model, 'user_id_mapping') else 0,
                "n_items": len(model.item_id_mapping) if hasattr(model, 'item_id_mapping') else 0,
            }

        return {
            "loaded_models_count": len(self.loaded_models),
            "training_sessions_count": len(self.training_states),
            "loaded_model_ids": list(self.loaded_models.keys()),
            "training_model_ids": list(self.training_states.keys()),
            "model_details": model_details,
            "available_algorithms": self.get_available_algorithms(),
            "available_model_types": self.get_available_model_types(),
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "service_info": {
                "models_directory": str(self.models_dir),
                "supported_algorithms": self.get_algorithm_details(),
                "available_model_types": [
                    {
                        "type": model_type,
                        "info": self.get_model_info_by_type(model_type)
                    }
                    for model_type in self.get_available_model_types()
                ],
            },
            "memory_info": self.get_memory_usage_info(),
            "disk_info": {
                "models_on_disk": len(list(self.models_dir.glob("*.pkl"))),
                "config_files": len(list(self.models_dir.glob("*_config.json"))),
            }
        }

    def validate_algorithm_parameters(
            self, algorithm: str, hyperparameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and suggest parameters for algorithms"""
        try:
            if algorithm not in self.supported_algorithms:
                return {
                    "valid": False,
                    "error": f"Unsupported algorithm: {algorithm}",
                    "available": list(self.supported_algorithms.keys())
                }

            algo_config = self.supported_algorithms[algorithm]
            model_type = algo_config["model_type"]

            # Get default parameters
            default_params = {k: v for k, v in algo_config.items() if k != "model_type"}

            # Validation rules for different model types
            validation_rules = {
                "nmf": {
                    "n_components": (1, 1000, int),
                    "max_iter": (1, 10000, int),
                    "solver": (["mu", "cd"], None, str),
                    "alpha": (0.0, 10.0, float),
                    "l1_ratio": (0.0, 1.0, float),
                },
                "svd": {
                    "n_components": (1, 1000, int),
                    "algorithm": (["randomized", "arpack"], None, str),
                    "n_iter": (1, 100, int),
                    "tol": (0.0, 1.0, float),
                }
            }

            rules = validation_rules.get(model_type, {})
            validated_params = default_params.copy()
            warnings = []
            errors = []

            for param, value in hyperparameters.items():
                if param in rules:
                    min_val, max_val, expected_type = rules[param]

                    # Type checking
                    if not isinstance(value, expected_type):
                        try:
                            value = expected_type(value)
                        except (ValueError, TypeError):
                            errors.append(f"{param}: Expected {expected_type.__name__}, got {type(value).__name__}")
                            continue

                    # Range/choices validation
                    if isinstance(min_val, list):  # Choices
                        if value not in min_val:
                            errors.append(f"{param}: Must be one of {min_val}, got {value}")
                            continue
                    else:  # Range
                        if min_val is not None and value < min_val:
                            errors.append(f"{param}: Must be >= {min_val}, got {value}")
                            continue
                        if max_val is not None and value > max_val:
                            errors.append(f"{param}: Must be <= {max_val}, got {value}")
                            continue

                    validated_params[param] = value
                else:
                    warnings.append(f"{param}: Not recognized for {model_type} model")
                    validated_params[param] = value

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validated_parameters": validated_params,
                "default_parameters": default_params,
                "algorithm": algorithm,
                "model_type": model_type,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
