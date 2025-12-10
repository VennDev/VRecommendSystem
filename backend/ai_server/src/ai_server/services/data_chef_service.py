import json
import os
from enum import Enum
from typing import Any, Dict, Generator, Optional

import loguru
import pandas as pd
import requests
from confluent_kafka import Consumer
from omegaconf import DictConfig, OmegaConf
from sqlalchemy import text, create_engine
from sqlalchemy.pool import QueuePool
from pymongo import MongoClient

from ai_server.config import config
from ai_server.config.config import Config
from ai_server.services.database_service import DatabaseService
from ai_server.utils.result_processing import rename_columns


def get_batch_size() -> int:
    return config.Config().get_config().datachef.batch_size


def _create_custom_sql_engine(db_config: Dict[str, Any]):
    """
    Create a custom SQL engine from database configuration.

    :param db_config: Database configuration dictionary
    :return: SQLAlchemy engine
    """
    db_type = db_config.get("type", "mysql")
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 3306)
    user = db_config.get("user", "root")
    password = db_config.get("password", "")
    database = db_config.get("database", "")
    ssl = db_config.get("ssl", False)

    # Build connection string
    if db_type.lower() == "postgresql":
        ssl_param = "?sslmode=require" if ssl else ""
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}{ssl_param}"
    elif db_type.lower() == "mysql":
        ssl_param = "?ssl=true" if ssl else ""
        connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}{ssl_param}"
    elif db_type.lower() == "sqlite":
        connection_string = f"sqlite:///{database}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    # Create engine
    engine = create_engine(
        connection_string,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30.0,
        pool_pre_ping=True,
    )

    return engine


def _create_custom_nosql_client(db_config: Dict[str, Any]):
    """
    Create a custom NoSQL client from database configuration.

    :param db_config: Database configuration dictionary
    :return: MongoDB client
    """
    db_type = db_config.get("type", "mongodb")
    if db_type.lower() != "mongodb":
        raise ValueError(f"Unsupported NoSQL database type: {db_type}")

    host = db_config.get("host", "localhost")
    port = db_config.get("port", 27017)
    username = db_config.get("username", "")
    password = db_config.get("password", "")
    ssl = db_config.get("ssl", False)
    auth_source = db_config.get("auth_source", "admin")

    # Build connection string
    if username and password:
        connection_string = f"mongodb://{username}:{password}@{host}:{port}"
    else:
        connection_string = f"mongodb://{host}:{port}"

    # Add query parameters
    params = []
    if auth_source:
        params.append(f"authSource={auth_source}")
    if ssl:
        params.append("ssl=true")

    if params:
        connection_string += "?" + "&".join(params)

    # Create client
    client = MongoClient(
        connection_string,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

    return client


class DataType(str, Enum):
    """
    Enumeration of supported data types.
    """

    SQL = "sql"
    NOSQL = "nosql"
    CSV = "csv"
    API = "api"
    MESSAGING_QUEUE = "messaging_queue"
    CUSTOM = "custom"


def _cook_sql(query: str, db_config: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Execute SQL query and yield results as dictionaries.

    :param query: SQL query string to execute.
    :param db_config: Optional database configuration. If not provided, uses default from local.yaml
    :return: Generator yielding rows from the SQL query result as dictionaries.
    :raises ValueError: If the query execution fails.
    """
    if not query or query.strip() == "":
        raise ValueError("SQL query is empty or not provided")

    # Use custom database config if provided, otherwise use default
    if db_config:
        engine = _create_custom_sql_engine(db_config)
    else:
        engine = DatabaseService().get_sql()

    try:
        with engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(text(query))

            # Get column names for creating dictionaries
            columns = list(result.keys())

            while True:
                chunk = result.fetchmany(get_batch_size())
                if not chunk:
                    break

                # Convert each row to dictionary
                for row in chunk:
                    yield dict(zip(columns, row))

    except Exception as e:
        raise ValueError(
            f"An error occurred while querying the SQL database: {e}"
        ) from e
    finally:
        if db_config:
            engine.dispose()


def _cook_nosql(
    database: str, collection: str, db_config: Optional[Dict[str, Any]] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Query a NoSQL database and yield results as dictionaries.

    :param database: Database name
    :param collection: Collection name
    :param db_config: Optional database configuration. If not provided, uses default from local.yaml
    :return: Generator yielding documents from the NoSQL collection as dictionaries.
    :raises ValueError: If the collection is not found or if an error occurs.
    """
    if not database or database.strip() == "":
        raise ValueError("NoSQL database name is empty or not provided")
    if not collection or collection.strip() == "":
        raise ValueError("NoSQL collection name is empty or not provided")

    # Use custom database config if provided, otherwise use default
    if db_config:
        client = _create_custom_nosql_client(db_config)
    else:
        client = DatabaseService().get_nosql()

    db = client[database]
    coln = db[collection]

    if not coln:
        raise ValueError(f"Collection {collection} not found in database {database}")

    try:
        batch_size = get_batch_size()
        skip_count = 0

        while True:
            chunk = list(coln.find().skip(skip_count).limit(batch_size))
            if not chunk:
                break

            # Convert MongoDB documents to dictionaries
            for doc in chunk:
                # Convert ObjectId to string if present
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                yield dict(doc)

            skip_count += batch_size

    except Exception as e:
        raise ValueError(
            f"An error occurred while querying the NoSQL database: {e}"
        ) from e
    finally:
        if db_config:
            client.close()


def _cook_csv(path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Read a CSV file in chunks and yield each row as a dictionary.

    :param path: Path to the CSV file
    :return: Generator yielding rows from the CSV file as dictionaries.
    :raises ValueError: If file didn't find or invalid CSV.
    """
    if not path or path.strip() == "":
        raise ValueError("CSV file path is empty or not provided")

    try:
        for chunk in pd.read_csv(path, chunksize=get_batch_size()):
            # Convert to records (list of dicts) then yield each dict
            records = chunk.to_dict(orient="records")
            for record in records:
                # Ensure all values are JSON serializable
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.NaT.__class__)):
                        cleaned_record[key] = str(value) if not pd.isna(value) else None
                    else:
                        cleaned_record[key] = value
                yield cleaned_record

    except FileNotFoundError as e:
        raise ValueError(f"CSV file not found at path: {path}") from e
    except pd.errors.EmptyDataError as e:
        raise ValueError("CSV file is empty or invalid.") from e
    except Exception as e:
        raise ValueError(f"An error occurred while reading the CSV file: {e}") from e


def _cook_api(url: str) -> Generator[Dict[str, Any], None, None]:
    """
    Query an API endpoint that returns a stream of JSON objects.

    :param url: URL of the API endpoint to query.
    :return: Generator yielding JSON objects from the API response as dictionaries.
    :raises ValueError: If the API request fails or if the response is not valid JSON.
    """
    if not url or url.strip() == "":
        raise ValueError("API URL is empty or not provided")

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                try:
                    json_obj = json.loads(line.decode("utf-8"))

                    # Ensure we always yield a dictionary
                    if isinstance(json_obj, dict):
                        yield json_obj
                    elif isinstance(json_obj, list):
                        # If it's a list, yield each item as dict (if possible)
                        for item in json_obj:
                            if isinstance(item, dict):
                                yield item
                            else:
                                # Wrap non-dict items in a dict
                                yield {"value": item}
                    else:
                        # Wrap primitive values in a dict
                        yield {"value": json_obj}

                except json.JSONDecodeError:
                    continue

    except requests.RequestException as e:
        raise ValueError(f"API request failed: {e}") from e


def _cook_api_paginated(
    base_url: str,
    page_param: str = "page",
    size_param: str = "size",
    page_size: int = 100,
) -> Generator[Dict[str, Any], None, None]:
    """
    Query a paginated API endpoint and yield results as dictionaries.

    :param base_url: Base URL of the API endpoint
    :param page_param: Parameter name for page number
    :param size_param: Parameter name for page size
    :param page_size: Number of items per page
    :return: Generator yielding JSON objects from the API response as dictionaries.
    :raises ValueError: If the API request fails.
    """
    if not base_url or base_url.strip() == "":
        raise ValueError("Paginated API base URL is empty or not provided")

    page = 1

    while True:
        try:
            # Build URL with pagination parameters
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}{page_param}={page}&{size_param}={page_size}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Handle different response formats
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                # Common pagination response formats
                if "items" in data:
                    items = data["items"]
                elif "data" in data:
                    items = data["data"]
                elif "results" in data:
                    items = data["results"]
                else:
                    # If single object, treat as single item
                    items = [data]

            # If no items, we've reached the end
            if not items:
                break

            # Yield each item as a dictionary
            for item in items:
                if isinstance(item, dict):
                    yield item
                else:
                    yield {"value": item}

            # Check if there are more pages
            if isinstance(data, dict):
                # Check various pagination indicators
                if data.get("has_next") is False:
                    break
                if data.get("next") is None:
                    break
                if len(items) < page_size:
                    break
            elif len(items) < page_size:
                break

            page += 1

        except requests.RequestException as e:
            raise ValueError(f"API request failed on page {page}: {e}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response on page {page}: {e}") from e


def _cook_messaging_queue(
    brokers: Optional[str] = None,
    topic: Optional[str] = None,
    group_id: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Connect to a messaging queue (e.g., Kafka) and yield messages as dictionaries.

    :param brokers: Comma-separated list of broker addresses (default: from KAFKA_BOOTSTRAP_SERVERS env)
    :param topic: Topic to subscribe to
    :param group_id: Consumer group ID (default: from KAFKA_GROUP_ID env or "data_chef_group")
    :return: Generator yielding messages from the queue as dictionaries.
    :raises ValueError: If connection fails or message processing fails.
    """
    # Use environment variables as fallback
    if not brokers:
        brokers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093")
    if not topic:
        topic = os.getenv("KAFKA_DEFAULT_TOPIC", "interactions")
    if not group_id:
        group_id = os.getenv("KAFKA_GROUP_ID", "data_chef_group")

    if not brokers or brokers.strip() == "":
        raise ValueError("Messaging queue brokers address is empty or not provided")
    if not topic or topic.strip() == "":
        raise ValueError("Messaging queue topic is empty or not provided")

    conf = {
        "bootstrap.servers": brokers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])

    loguru.logger.info(
        f"Kafka consumer subscribed to topic '{topic}' with group '{group_id}' on brokers '{brokers}'"
    )

    # Timeout configuration: stop consuming after N seconds of no new messages
    empty_polls = 0
    max_empty_polls = 30  # 30 seconds with no messages = stop consuming
    messages_received = 0
    messages_yielded = 0

    try:
        while True:
            msg = consumer.poll(1.0)  # Timeout of 1 second

            if msg is None:
                empty_polls += 1
                if empty_polls >= max_empty_polls:
                    # No new messages for max_empty_polls seconds, stop consuming
                    loguru.logger.info(
                        f"Kafka consumer timeout after {max_empty_polls}s. Total messages: received={messages_received}, yielded={messages_yielded}"
                    )
                    break
                continue

            # Reset counter when we receive a message
            empty_polls = 0
            messages_received += 1
            loguru.logger.debug(
                f"Kafka message #{messages_received} received from topic '{topic}'"
            )
            if msg.error():
                raise ValueError(f"Consumer error: {msg.error()}")

            try:
                message_value = msg.value().decode("utf-8")
                json_obj = json.loads(message_value)
                loguru.logger.debug(f"Kafka message parsed successfully: {json_obj}")

                # Ensure we always yield a dictionary
                if isinstance(json_obj, dict):
                    messages_yielded += 1
                    loguru.logger.debug(
                        f"Yielding message #{messages_yielded}: {json_obj}"
                    )
                    yield json_obj
                elif isinstance(json_obj, list):
                    for item in json_obj:
                        if isinstance(item, dict):
                            messages_yielded += 1
                            loguru.logger.debug(
                                f"Yielding message #{messages_yielded} from list: {item}"
                            )
                            yield item
                        else:
                            messages_yielded += 1
                            loguru.logger.debug(
                                f"Yielding message #{messages_yielded} as wrapped value"
                            )
                            yield {"value": item}
                else:
                    messages_yielded += 1
                    loguru.logger.debug(
                        f"Yielding message #{messages_yielded} as wrapped value"
                    )
                    yield {"value": json_obj}

            except json.JSONDecodeError as e:
                loguru.logger.warning(
                    f"Failed to parse Kafka message as JSON: {e}. Message: {message_value[:100]}"
                )
                continue

    except Exception as e:
        loguru.logger.error(
            f"Kafka consumer error after {messages_received} messages: {e}"
        )
        raise ValueError(f"An error occurred while consuming messages: {e}") from e
    finally:
        loguru.logger.info(
            f"Kafka consumer closing. Total: received={messages_received}, yielded={messages_yielded}"
        )
        consumer.close()


def _cook_raw_data_source(
    source_type: str, **kwargs
) -> Generator[Dict[str, Any], None, None]:
    """
    Unified interface for all data sources.

    :param source_type: Type of data source ('sql', 'nosql', 'csv', 'api')
    :param kwargs: Arguments specific to each data source type
    :return: Generator yielding dictionaries from any data source
    """
    db_config = kwargs.get("db_config", None)

    if source_type == "sql":
        yield from _cook_sql(kwargs["query"], db_config)
    elif source_type == "nosql":
        yield from _cook_nosql(kwargs["database"], kwargs["collection"], db_config)
    elif source_type == "csv":
        yield from _cook_csv(kwargs["path"])
    elif source_type == "api":
        if kwargs.get("paginated", False):
            yield from _cook_api_paginated(
                kwargs["url"],
                kwargs.get("page_param", "page"),
                kwargs.get("size_param", "size"),
                kwargs.get("page_size", 100),
            )
        else:
            yield from _cook_api(kwargs["url"])
    elif source_type == "messaging_queue":
        yield from _cook_messaging_queue(
            kwargs["brokers"],
            kwargs["topic"],
            kwargs.get("group_id", "data_chef_group"),
        )
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


def _mask_sensitive_value(value: str, show_chars: int = 3) -> str:
    """
    Mask a sensitive value, showing only the first N characters.

    :param value: The value to mask
    :param show_chars: Number of characters to show from the beginning
    :return: Masked value
    """
    if not value or len(value) <= show_chars:
        return "*" * len(value) if value else ""
    return value[:show_chars] + "*" * (len(value) - show_chars)


def _mask_db_config(db_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive fields in database configuration.

    :param db_config: Database configuration dictionary
    :return: Masked database configuration
    """
    if not db_config:
        return {}

    masked_config = db_config.copy()

    # Mask password
    if "password" in masked_config:
        masked_config["password"] = _mask_sensitive_value(masked_config["password"], 3)

    # Mask hostname (show first 3 chars)
    if "host" in masked_config:
        masked_config["host"] = _mask_sensitive_value(masked_config["host"], 3)

    # Mask username (show first 3 chars)
    if "username" in masked_config:
        masked_config["username"] = _mask_sensitive_value(masked_config["username"], 3)

    if "user" in masked_config:
        masked_config["user"] = _mask_sensitive_value(masked_config["user"], 3)

    return masked_config


class DataChefService:
    """
    Service for cooking data from various sources.
    """

    def __init__(self):
        pass

    def cook(self, name: str) -> Generator[Dict[str, Any], None, None]:
        loguru.logger.info(name)
        """
        Cook data based on the configuration name provided.

        :param name: Name of the configuration to use for cooking data.
        :return: Generator yielding dictionaries from the data source.
        :raises ValueError: If the configuration is not found or if the data type is invalid
        """
        cfg = Config().get_config_safe("restaurant_data")
        data = cfg.get(name, None)
        if data is None:
            raise ValueError(f"Configuration for {name} not found in DataChefService")

        # Backward compatibility: map 'messaging' to 'messaging_queue'
        data_type = data["type"].lower()
        if data_type == "messaging":
            data_type = "messaging_queue"

        try:
            type_enum = DataType(data_type)
        except (ValueError, KeyError) as e:
            data_type = (
                data.get("type", "unknown")
                if isinstance(data, dict)
                else getattr(data, "type", "unknown")
            )
            raise ValueError(
                f"Invalid data type: {data_type}. Must be one of {[t.value for t in DataType]}."
            ) from e

        for value in _cook_raw_data_source(type_enum, **data):
            # Rename columns if specified in the configuration
            if "rename_columns" in data:
                value = rename_columns(value, data["rename_columns"])
            yield value

    def _merge_config(self, name: str, new_data: dict) -> None:
        """
        Helper method to properly merge configuration data.

        :param name: Name of the configuration
        :param new_data: New data to merge
        """
        # Get existing config
        existing_cfg = Config().get_config_safe("restaurant_data")

        # Convert to regular dict if it's a DictConfig
        if isinstance(existing_cfg, DictConfig):
            existing_dict = OmegaConf.to_object(existing_cfg)
        else:
            existing_dict = existing_cfg if existing_cfg else {}

        # Update with new data
        existing_dict[name] = new_data

        # Save the updated configuration
        Config().set_config_with_dict("restaurant_data", existing_dict)

    def create_data_chef_csv(self, name: str, path: str, rename_columns: str) -> None:
        """
        Create a CSV data chef configuration.

        :param name: Name of the configuration
        :param path: Path to the CSV file
        :param rename_columns: string of columns to rename in the format "old1:new1,old2:new2"
        """
        new_data = {
            "type": DataType.CSV.value,
            "path": path,
            "rename_columns": rename_columns,
        }
        self._merge_config(name, new_data)

    def create_data_chef_sql(self, name: str, query: str, rename_columns: str, db_config: Optional[Dict[str, Any]] = None) -> None:
        """
        Create an SQL data chef configuration.

        :param name:
        :param query:
        :param rename_columns:
        :param db_config: Optional database configuration for this data chef
        :return:
        """
        new_data = {
            "type": DataType.SQL.value,
            "query": query,
            "rename_columns": rename_columns,
        }

        if db_config:
            new_data["db_config"] = db_config

        self._merge_config(name, new_data)

    def create_data_chef_nosql(
        self, name: str, database: str, collection: str, rename_columns: str, db_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create a NoSQL data chef configuration.

        :param name:
        :param database:
        :param collection:
        :param rename_columns:
        :param db_config: Optional database configuration for this data chef
        :return:
        """
        new_data = {
            "type": DataType.NOSQL.value,
            "database": database,
            "collection": collection,
            "rename_columns": rename_columns,
        }

        if db_config:
            new_data["db_config"] = db_config

        self._merge_config(name, new_data)

    def create_data_chef_api(
        self,
        name: str,
        url: str,
        rename_columns: str,
        paginated: bool = False,
        page_param: str = "page",
        size_param: str = "size",
        page_size: int = 100,
    ) -> None:
        """
        Create an API data chef configuration.

        :param name:
        :param url:
        :param rename_columns:
        :param paginated:
        :param page_param:
        :param size_param:
        :param page_size:
        :return:
        """
        new_data = {
            "type": DataType.API.value,
            "url": url,
            "paginated": paginated,
            "rename_columns": rename_columns,
        }
        if paginated:
            new_data["page_param"] = page_param
            new_data["size_param"] = size_param
            new_data["page_size"] = page_size

        self._merge_config(name, new_data)

    def create_data_chef_messaging_queue(
        self,
        name: str,
        brokers: str,
        topic: str,
        rename_columns: str,
        group_id: str = "data_chef_group",
    ) -> None:
        """
        Create a messaging queue data chef configuration.

        :param name:
        :param brokers:
        :param topic:
        :param rename_columns:
        :param group_id:
        :return:
        """
        new_data = {
            "type": DataType.MESSAGING_QUEUE.value,
            "brokers": brokers,
            "topic": topic,
            "group_id": group_id,
            "rename_columns": rename_columns,
        }
        self._merge_config(name, new_data)

    def list_data_chefs(self, mask_sensitive: bool = True) -> dict:
        """
        List all data chef configurations.

        :param mask_sensitive: Whether to mask sensitive information like passwords
        :return: Dictionary of all data chef configurations.
        """
        cfg = Config().get_config_safe("restaurant_data")
        if isinstance(cfg, DictConfig):
            config_dict = OmegaConf.to_object(cfg)
        else:
            config_dict = cfg if cfg else {}

        # Mask sensitive information if requested
        if mask_sensitive:
            masked_dict = {}
            for name, chef_config in config_dict.items():
                masked_chef = chef_config.copy()
                if "db_config" in masked_chef:
                    masked_chef["db_config"] = _mask_db_config(masked_chef["db_config"])
                masked_dict[name] = masked_chef
            return masked_dict

        return config_dict

    def edit_data_chef(self, name: str, config_dict: dict) -> None:
        """
        Edit an existing data chef configuration.

        :param name: Name of the configuration to edit.
        :param config_dict: Dictionary of configuration parameters to update.
        :raises ValueError: If the configuration does not exist.
        """
        # Get existing config
        existing_cfg = Config().get_config_safe("restaurant_data")

        # Convert to dict if needed
        if isinstance(existing_cfg, DictConfig):
            existing_dict = OmegaConf.to_object(existing_cfg)
        else:
            existing_dict = existing_cfg if existing_cfg else {}

        if name not in existing_dict:
            raise ValueError(f"Configuration for {name} not found in DataChefService")

        # Update the existing entry with new values
        for key, value in config_dict.items():
            if value is None:
                # Remove the key if value is None
                existing_dict[name].pop(key, None)
            else:
                existing_dict[name][key] = value

        # Save the updated configuration
        Config().set_config_with_dict("restaurant_data", existing_dict)

    def delete_data_chef(self, name: str) -> None:
        """
        Delete a data chef configuration.

        :param name:
        :return:
        """
        existing_cfg = Config().get_config_safe("restaurant_data")

        # Convert to dict if needed
        if isinstance(existing_cfg, DictConfig):
            existing_dict = OmegaConf.to_object(existing_cfg)
        else:
            existing_dict = existing_cfg if existing_cfg else {}

        if name not in existing_dict:
            raise ValueError(f"Configuration for {name} not found in DataChefService")

        # Delete the entry
        del existing_dict[name]

        # Save the updated configuration
        Config().set_config_with_dict("restaurant_data", existing_dict)

    def get_data_chef(self, name: str, mask_sensitive: bool = True) -> Dict[str, Any]:
        """
        Get a specific data chef configuration.

        :param name: Name of the data chef
        :param mask_sensitive: Whether to mask sensitive information like passwords
        :return: Dictionary of the specified data chef configuration.
        :raises ValueError: If the configuration does not exist.
        """
        cfg = Config().get_config_safe("restaurant_data")

        # Convert to dict if needed
        if isinstance(cfg, DictConfig):
            config_dict = OmegaConf.to_object(cfg)
        else:
            config_dict = cfg if cfg else {}

        if name not in config_dict:
            raise ValueError(f"Configuration for {name} not found in DataChefService")

        data_chef = config_dict[name].copy()

        # Mask sensitive information if requested
        if mask_sensitive and "db_config" in data_chef:
            data_chef["db_config"] = _mask_db_config(data_chef["db_config"])

        return data_chef

    def get_total_data_chefs(self) -> int:
        """
        Get the total number of data chef configurations.

        :return: Total count of data chef configurations.
        """
        cfg = Config().get_config_safe("restaurant_data")
        if isinstance(cfg, DictConfig):
            config_dict = OmegaConf.to_object(cfg)
        else:
            config_dict = cfg if cfg else {}
        return len(config_dict)
