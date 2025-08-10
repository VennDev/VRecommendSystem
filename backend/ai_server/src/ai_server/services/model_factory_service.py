import datetime
from ..database.nosql import NoSQLDatabase
from ..database.sql import SQLDatabase
from ..services.model_service import ModelService
from ..services.database_service import DatabaseService
from ..utils.result_processing import rename_columns, list_dict_to_dataframe


class ModelFactoryService:
    """
    Service class for creating and managing recommendation models.
    Provides methods to create, train, and evaluate models using various algorithms.
    Supports both file-based datasets and in-memory DataFrames.
    """

    def __init__(self):
        self.model_service = ModelService()

    def create_model(self, fetch_data_type: str, **kwargs) -> None:
        """
        Create a new recommendation model.

        Args:
            fetch_data_type: Type of data to fetch ("messaging", "database", "file", "dataframe")
            **kwargs: Additional parameters for model creation
        Returns:
            ModelService instance with the created model
        """
        # Create model config
        model_id = kwargs.get(
            "model_id", f"model_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        algorithm = kwargs.get("algorithm", "als")
        hyperparameters = kwargs.get("hyperparameters", {})

        if fetch_data_type in ["file", "dataframe"]:
            # Handle file or DataFrame input
            dataset_source = kwargs.get("dataset_source")
            if dataset_source is None:
                raise ValueError(
                    "dataset_source must be provided for file/dataframe input"
                )

            # Load dataset
            data = self.model_service.load_dataset(dataset_source)
            config = self.model_service.create_model_config(
                model_id=model_id,
                algorithm=algorithm,
                hyperparameters=hyperparameters,
                dataset_source=data,
            )

            # Train model
            self.model_service.train_model(model_id, config)
        elif fetch_data_type == "database":
            query_string = kwargs.get("query_string")
            transform_map = kwargs.get("transform_map", None)
            database_service = DatabaseService().get_database()
            data = None
            if isinstance(database_service, SQLDatabase):
                data = database_service.execute_query(query_string)
            if isinstance(database_service, NoSQLDatabase):
                data = list(database_service.get_collection(query_string).find({}))
            if data is not None and transform_map is not None and isinstance(transform_map, str):
                data = list_dict_to_dataframe(rename_columns(data, transform_map))
            if not data:
                raise ValueError("No data returned from the database query")

            config = self.model_service.create_model_config(
                model_id=model_id,
                algorithm=algorithm,
                hyperparameters=hyperparameters,
                dataset_source=data,
            )

            # Train model
            self.model_service.train_model(model_id, config)
