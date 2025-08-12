import json

import loguru
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Type
from datetime import datetime

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
    ModelInfo,
    ModelTrainingResult,
    ModelPredictResult,
    ModelPredictScoresResult,
    ModelStatus,
)


class ModelService:
    """
    Service class for managing recommendation models.
    Handles training, loading, saving, and prediction operations.
    Supports both file-based datasets and in-memory DataFrames.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # In-memory model cache
        self.loaded_models: Dict[str, BaseRecommender] = {}

        # Model configuration storage
        self.model_configs: Dict[str, Dict[str, Any]] = {}

        # In-memory dataset cache
        self.cached_datasets: Dict[str, pd.DataFrame] = {}

        # Initialize model registry
        self.model_registry: Dict[str, Type[BaseRecommender]] = {
            "als": ALSRecommender,
            "bpr": BPRRecommender,
            "ncf": NCFRecommender,
            "tfidf": TFIDFRecommender,
            "feature": FeatureBasedRecommender,
        }

    def register_dataset(self, dataset_name: str, data: pd.DataFrame) -> str:
        """
        Register a DataFrame as a dataset for later use.

        Args:
            dataset_name: Name to identify this dataset
            data: DataFrame to register

        Returns:
            Dataset identifier that can be used in model configs
        """
        self.cached_datasets[dataset_name] = data.copy()
        loguru.logger.info(f"Registered dataset '{dataset_name}' with {len(data)} records")
        return dataset_name

    def load_dataset(self, dataset_source: Union[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Load dataset from various sources.

        Args:
            dataset_source: Can be:
                - File path (str): Load from file
                - Dataset name (str): Load from cached datasets
                - DataFrame: Return as-is

        Returns:
            DataFrame with the data
        """
        try:
            # If it's already a DataFrame, return it
            if isinstance(dataset_source, pd.DataFrame):
                loguru.logger.info(
                    f"Using provided DataFrame with {len(dataset_source)} records"
                )
                return dataset_source.copy()

            # Check if it's a cached dataset name
            if dataset_source in self.cached_datasets:
                data = self.cached_datasets[dataset_source].copy()
                loguru.logger.info(
                    f"Loaded cached dataset '{dataset_source}' with {len(data)} records"
                )
                return data

            # Try to load as a file path
            if os.path.exists(dataset_source):
                if dataset_source.endswith(".csv"):
                    data = pd.read_csv(dataset_source)
                elif dataset_source.endswith(".parquet"):
                    data = pd.read_parquet(dataset_source)
                elif dataset_source.endswith(".json"):
                    data = pd.read_json(dataset_source)
                else:
                    raise ValueError(f"Unsupported file format: {dataset_source}")

                loguru.logger.info(
                    f"Loaded dataset from file '{dataset_source}' with {len(data)} records"
                )
                return data

            raise FileNotFoundError(f"Dataset source not found: {dataset_source}")

        except Exception as e:
            loguru.logger.error(f"Error loading dataset from {dataset_source}: {str(e)}")
            raise

    def get_model_class(self, algorithm: str) -> Type[BaseRecommender]:
        """Get model class by algorithm name."""
        if algorithm not in self.model_registry:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. Available: {list(self.model_registry.keys())}"
            )

        return self.model_registry[algorithm]

    def create_model_config(
            self,
            model_id: str,
            model_name: str,
            message: str,
            algorithm: str,
            hyperparameters: Optional[Dict[str, Any]] = None,
            dataset_source: Optional[Union[str, pd.DataFrame]] = None,
            user_features_source: Optional[Union[str, pd.DataFrame]] = None,
            item_features_source: Optional[Union[str, pd.DataFrame]] = None,
            query_string: Optional[str] = None,
    ) -> ModelInfo:
        """
        Create and store model configuration.

        Args:
            model_id: Unique identifier for the model
            model_name: User-friendly name for the model
            message: Description or message about the model
            algorithm: Algorithm name
            hyperparameters: Model hyperparameters
            dataset_source: Dataset source (file path, cached dataset name, or DataFrame)
            user_features_source: User features source
            item_features_source: Item features source
            query_string: Optional query string for database input
        Returns:
            ModelInfo object with the created model configuration
        """

        # Handle DataFrame inputs by caching them
        dataset_ref = self._handle_dataset_source(
            f"{model_id}_interactions", dataset_source
        )
        user_features_ref = self._handle_dataset_source(
            f"{model_id}_user_features", user_features_source
        )
        item_features_ref = self._handle_dataset_source(
            f"{model_id}_item_features", item_features_source
        )

        config = {
            "model_id": model_id,
            "model_name": model_name,
            "message": message,
            "algorithm": algorithm,
            "hyperparameters": hyperparameters or {},
            "dataset_source": dataset_ref,
            "user_features_source": user_features_ref,
            "item_features_source": item_features_ref,
            "created_at": datetime.now().isoformat(),
            "status": ModelStatus.COMPLETED,
            "model_path": str(self.models_dir / f"{model_id}.pkl"),
            "training_started_at": None,
            "training_completed_at": None,
            "training_time": 60.0,  # Default to 60 seconds
            "query_string": query_string,
        }

        self.model_configs[model_id] = config

        # Save config to file
        config_path = self.models_dir / f"{model_id}_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        loguru.logger.info(f"Created configuration for model {model_id}")
        return ModelInfo(**config)

    def _handle_dataset_source(
            self, cache_name: str, dataset_source: Optional[Union[str, pd.DataFrame]]
    ) -> Optional[str]:
        """
        Handle a dataset source and return a reference string.

        Args:
            cache_name: Name to use for caching if it's a DataFrame
            dataset_source: The dataset source

        Returns:
            Reference string that can be used to load the dataset later
        """
        if dataset_source is None:
            return None

        if isinstance(dataset_source, pd.DataFrame):
            # Cache the DataFrame and return the cache name
            self.cached_datasets[cache_name] = dataset_source.copy()
            return cache_name

        # If it's a string, return as-is (could be file path or existing cache name)
        return dataset_source

    def train_model_from_data(
            self,
            model_id: str,
            model_name: str,
            message: str,
            algorithm: str,
            interaction_data: pd.DataFrame,
            user_features: Optional[pd.DataFrame] = None,
            item_features: Optional[pd.DataFrame] = None,
            hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> ModelInfo:
        """
        Train a model directly from DataFrames.

        Args:
            model_id: Unique identifier for the model
            model_name: User-friendly name for the model
            message: Description or message about the model
            algorithm: Algorithm name
            interaction_data: Interaction data DataFrame
            user_features: Optional user features DataFrame
            item_features: Optional item features DataFrame
            hyperparameters: Model hyperparameters

        Returns:
            ModelInfo object with training details
        """
        try:
            loguru.logger.info(f"Training model {model_id} directly from DataFrames")

            # Create config with DataFrames
            config = self.create_model_config(
                model_id=model_id,
                model_name=model_name,
                message=message,
                algorithm=algorithm,
                hyperparameters=hyperparameters,
                dataset_source=interaction_data,
                user_features_source=user_features,
                item_features_source=item_features,
            )

            # Train the model
            self.train_model(model_id, config.to_dict())
            return config
        except Exception as e:
            loguru.logger.error(f"Error training model from data {model_id}: {str(e)}")
            return ModelInfo(
                model_id=model_id,
                model_name=model_name,
                message=message,
                status=ModelStatus.FAILED
            )

    def train_model(
            self, model_id: str, config: Optional[Dict[str, Any]] = None
    ) -> ModelTrainingResult:
        """Train a model with a given configuration."""
        try:
            # Load or use provided config
            if config is None:
                if model_id not in self.model_configs:
                    config_path = self.models_dir / f"{model_id}_config.json"
                    if config_path.exists():
                        with open(config_path, "r") as f:
                            config = json.load(f)
                        self.model_configs[model_id] = config
                    else:
                        raise ValueError(f"No configuration found for model {model_id}")
                else:
                    config = self.model_configs[model_id]

            loguru.logger.info(
                f"Starting training for model {model_id} with algorithm {config['algorithm']}"
            )

            # Update status
            config["status"] = "training"
            config["training_started_at"] = datetime.now().isoformat()

            # Load datasets using the enhanced load_dataset method
            if not config.get("dataset_source"):
                raise ValueError(f"No dataset source specified for model {model_id}")

            interaction_data = self.load_dataset(config["dataset_source"])

            # Validate and preprocess data
            DataPreprocessor.validate_data_format(interaction_data)

            # Load additional features if specified
            user_features = None
            item_features = None

            if config.get("user_features_source"):
                user_features = self.load_dataset(config["user_features_source"])
                loguru.logger.info(f"Loaded user features: {user_features.shape}")

            if config.get("item_features_source"):
                item_features = self.load_dataset(config["item_features_source"])
                loguru.logger.info(f"Loaded item features: {item_features.shape}")

            # Initialize model
            model_class = self.get_model_class(config["algorithm"])
            model = model_class(**config["hyperparameters"])

            # Train model
            start_time = datetime.now()
            model.fit(interaction_data, user_features, item_features)
            training_time = (datetime.now() - start_time).total_seconds()

            # Save trained model
            model_path = config["model_path"]
            model.save(model_path)

            # Update configuration
            config["status"] = "trained"
            config["training_completed_at"] = datetime.now().isoformat()
            config["training_time"] = training_time
            config["model_metrics"] = model.get_metrics()

            # Cache model in memory
            self.loaded_models[model_id] = model

            # Save updated config
            config_path = self.models_dir / f"{model_id}_config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            loguru.logger.info(
                f"Model {model_id} trained successfully in {training_time:.2f}s"
            )

            return ModelTrainingResult(
                model_id=model_id,
                status="success",
                training_time=training_time,
                metrics=model.get_metrics(),
            )
        except Exception as e:
            # Update status to failed
            if model_id in self.model_configs:
                self.model_configs[model_id]["status"] = "failed"
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

            with open(config_path, "r") as f:
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

        except Exception as e:
            loguru.logger.error(f"Error loading model {model_id}: {str(e)}")
            raise

    def predict_with_model(
            self, model_id: str, user_id: Union[str, List[str]], top_k: int = 10
    ) -> ModelPredictResult:
        """Generate predictions with a trained model."""
        try:
            # Load model if not in memory
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Generate predictions
            if isinstance(user_id, str):
                user_ids = [user_id]
            else:
                user_ids = user_id

            predictions_df = model.predict(user_ids, n_recommendations=top_k)

            # Convert to desired output format
            predictions = {}
            for user in user_ids:
                user_predictions = predictions_df[predictions_df["user_id"] == user]
                predictions[user] = [
                    {"item_id": row["item_id"], "score": float(row["score"])}
                    for _, row in user_predictions.iterrows()
                ]

            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions=predictions,
                datetime=datetime.now().isoformat(),
                status=ModelStatus.COMPLETED,
            )
        except Exception as e:
            loguru.logger.error(f"Error predicting with model {model_id}: {str(e)}")
            return ModelPredictResult(
                model_id=model_id,
                user_id=user_id,
                predictions={},
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def predict_scores(
            self,
            model_id: str,
            user_ids: Union[str, List[str]],
            item_ids: Union[str, List[str]],
    ) -> ModelPredictScoresResult:
        """Predict scores for specific user-item pairs."""
        try:
            # Load model if not in memory
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Ensure inputs are lists
            if isinstance(user_ids, str):
                user_ids = [user_ids]
            if isinstance(item_ids, str):
                item_ids = [item_ids]

            # Check if lengths match
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

        except Exception as e:
            loguru.logger.error(f"Error predicting scores with model {model_id}: {str(e)}")
            return ModelPredictScoresResult(
                model_id=model_id,
                results=[],
                datetime=datetime.now().isoformat(),
                status=ModelStatus.FAILED,
            )

    def evaluate_model_from_data(
            self,
            model_id: str,
            test_data: pd.DataFrame,
            k_values: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model using test data DataFrame.

        Args:
            model_id: Model identifier
            test_data: Test data DataFrame
            k_values: K values for evaluation metrics

        Returns:
            Evaluation results
        """
        if k_values is None:
            k_values = [5, 10, 20]

        try:
            # Load model
            if model_id not in self.loaded_models:
                self.load_model(model_id)

            model = self.loaded_models[model_id]

            # Generate predictions for test users
            test_users = test_data["user_id"].unique()
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
            }

            loguru.logger.info(f"Evaluated model {model_id} on provided test data")
            return evaluation_results

        except Exception as e:
            loguru.logger.error(f"Error evaluating model {model_id}: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def evaluate_model(
            self,
            model_id: str,
            test_data_source: Union[str, pd.DataFrame],
            k_values: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a trained model.

        Args:
            model_id: Model identifier
            test_data_source: Test data source (file path, cached name, or DataFrame)
            k_values: K values for evaluation metrics
        """
        if k_values is None:
            k_values = [5, 10, 20]

        try:
            # Load test data using the enhanced load_dataset method
            test_data = self.load_dataset(test_data_source)

            # Use the DataFrame-based evaluation method
            return self.evaluate_model_from_data(model_id, test_data, k_values)

        except Exception as e:
            loguru.logger.error(f"Error evaluating model {model_id}: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        models = []

        # Check for config files in models directory
        for config_file in self.models_dir.glob("*_config.json"):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                model_info = {
                    "model_id": config["model_id"],
                    "algorithm": config["algorithm"],
                    "status": config["status"],
                    "created_at": config.get("created_at"),
                    "training_time": config.get("training_time"),
                    "metrics": config.get("model_metrics", {}),
                    "uses_cached_data": self._uses_cached_data(config),
                }

                models.append(model_info)

            except Exception as e:
                loguru.logger.warning(f"Error reading config {config_file}: {str(e)}")

        return models

    def _uses_cached_data(self, config: Dict[str, Any]) -> bool:
        """Check if model config uses cached data."""
        sources = [
            config.get("dataset_source"),
            config.get("user_features_source"),
            config.get("item_features_source"),
        ]

        return any(source in self.cached_datasets for source in sources if source)

    def list_cached_datasets(self) -> List[Dict[str, Any]]:
        """List all cached datasets."""
        datasets = []

        for name, data in self.cached_datasets.items():
            dataset_info = {
                "name": name,
                "shape": data.shape,
                "columns": list(data.columns),
                "memory_usage_mb": round(
                    data.memory_usage(deep=True).sum() / (1024 * 1024), 2
                ),
            }
            datasets.append(dataset_info)

        return datasets

    def clear_cached_dataset(self, dataset_name: str) -> bool:
        """Clear a specific cached dataset."""
        if dataset_name in self.cached_datasets:
            del self.cached_datasets[dataset_name]
            loguru.logger.info(f"Cleared cached dataset: {dataset_name}")
            return True
        return False

    def clear_all_cached_datasets(self) -> int:
        """Clear all cached datasets."""
        count = len(self.cached_datasets)
        self.cached_datasets.clear()
        loguru.logger.info(f"Cleared {count} cached datasets")
        return count

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

        except Exception as e:
            loguru.logger.error(f"Error deleting model {model_id}: {str(e)}")
            return {"model_id": model_id, "status": "error", "error": str(e)}

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information about a model."""
        try:
            config_path = self.models_dir / f"{model_id}_config.json"
            if not config_path.exists():
                raise FileNotFoundError(f"Model {model_id} not found")

            with open(config_path, "r") as f:
                config = json.load(f)

            # Check if a model file exists
            model_exists = os.path.exists(config["model_path"])

            # Get model in memory status
            in_memory = model_id in self.loaded_models

            model_info: dict[str, Any] = {
                **config,
                "model_file_exists": model_exists,
                "loaded_in_memory": in_memory,
                "file_size_mb": None,
                "uses_cached_data": self._uses_cached_data(config),
            }

            # Get file size if exists
            if model_exists:
                file_size = os.path.getsize(config["model_path"])
                model_info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

            return model_info

        except Exception as e:
            loguru.logger.error(f"Error getting model info {model_id}: {str(e)}")
            raise
