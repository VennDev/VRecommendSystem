import json
from enum import Enum
from typing import Generator, Dict, Any

import loguru
from omegaconf import OmegaConf, DictConfig
from sqlalchemy import text
import pandas as pd
import requests
from confluent_kafka import Consumer
from ai_server.utils.result_processing import rename_columns
from ai_server.services.database_service import DatabaseService
from ai_server.config.config import Config


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


def _cook_sql(query: str) -> Generator[Dict[str, Any], None, None]:
    """
    Execute SQL query and yield results as dictionaries.

    :param query: SQL query string to execute.
    :return: Generator yielding rows from the SQL query result as dictionaries.
    :raises ValueError: If the query execution fails.
    """
    service = DatabaseService().get_sql()
    try:
        with service.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(text(query))

            # Get column names for creating dictionaries
            columns = list(result.keys())

            while True:
                chunk = result.fetchmany(1000)
                if not chunk:
                    break

                # Convert each row to dictionary
                for row in chunk:
                    yield dict(zip(columns, row))

    except Exception as e:
        raise ValueError(
            f"An error occurred while querying the SQL database: {e}"
        ) from e


def _cook_nosql(
        database: str, collection: str
) -> Generator[Dict[str, Any], None, None]:
    """
    Query a NoSQL database and yield results as dictionaries.

    :param database: Database name
    :param collection: Collection name
    :return: Generator yielding documents from the NoSQL collection as dictionaries.
    :raises ValueError: If the collection is not found or if an error occurs.
    """
    service = DatabaseService().get_nosql()
    db = service[database]
    coln = db[collection]

    if not coln:
        raise ValueError(f"Collection {collection} not found in database {database}")

    try:
        batch_size = 1000
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


def _cook_csv(path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Read a CSV file in chunks and yield each row as a dictionary.

    :param path: Path to the CSV file
    :return: Generator yielding rows from the CSV file as dictionaries.
    :raises ValueError: If file didn't find or invalid CSV.
    """
    try:
        for chunk in pd.read_csv(path, chunksize=1000):
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
        brokers: str,
        topic: str,
        group_id: str = "data_chef_group"
) -> Generator[Dict[str, Any], None, None]:
    """
    Connect to a messaging queue (e.g., Kafka) and yield messages as dictionaries.

    :param brokers: Comma-separated list of broker addresses
    :param topic: Topic to subscribe to
    :param group_id: Consumer group ID
    :return: Generator yielding messages from the queue as dictionaries.
    :raises ValueError: If connection fails or message processing fails.
    """
    conf = {
        'bootstrap.servers': brokers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)  # Timeout of 1 second

            if msg is None:
                continue
            if msg.error():
                raise ValueError(f"Consumer error: {msg.error()}")

            try:
                message_value = msg.value(None).decode('utf-8')
                json_obj = json.loads(message_value)

                # Ensure we always yield a dictionary
                if isinstance(json_obj, dict):
                    yield json_obj
                elif isinstance(json_obj, list):
                    for item in json_obj:
                        if isinstance(item, dict):
                            yield item
                        else:
                            yield {"value": item}
                else:
                    yield {"value": json_obj}

            except json.JSONDecodeError:
                continue

    except Exception as e:
        raise ValueError(f"An error occurred while consuming messages: {e}") from e
    finally:
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
    if source_type == "sql":
        yield from _cook_sql(kwargs["query"])
    elif source_type == "nosql":
        yield from _cook_nosql(kwargs["database"], kwargs["collection"])
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
            kwargs.get("group_id", "data_chef_group")
        )
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


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

        try:
            type_enum = DataType(data["type"].lower())
        except (ValueError, KeyError) as e:
            data_type = data.get("type", "unknown") if isinstance(data, dict) else getattr(data, "type", "unknown")
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

    def create_data_chef_sql(self, name: str, query: str, rename_columns: str) -> None:
        """
        Create an SQL data chef configuration.

        :param name:
        :param query:
        :param rename_columns:
        :return:
        """
        new_data = {
            "type": DataType.SQL.value,
            "query": query,
            "rename_columns": rename_columns,
        }
        self._merge_config(name, new_data)

    def create_data_chef_nosql(self, name: str, database: str, collection: str,
                               rename_columns: str) -> None:
        """
        Create a NoSQL data chef configuration.

        :param name:
        :param database:
        :param collection:
        :param rename_columns:
        :return:
        """
        new_data = {
            "type": DataType.NOSQL.value,
            "database": database,
            "collection": collection,
            "rename_columns": rename_columns,
        }
        self._merge_config(name, new_data)

    def create_data_chef_api(self, name: str, url: str, rename_columns: str, paginated: bool = False,
                             page_param: str = "page", size_param: str = "size", page_size: int = 100,
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

    def create_data_chef_messaging_queue(self, name: str, brokers: str, topic: str,
                                         rename_columns: str, group_id: str = "data_chef_group") -> None:
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

    def list_data_chefs(self) -> dict:
        """
        List all data chef configurations.

        :return: Dictionary of all data chef configurations.
        """
        cfg = Config().get_config_safe("restaurant_data")
        if isinstance(cfg, DictConfig):
            return OmegaConf.to_object(cfg)
        return cfg if cfg else {}

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
        existing_dict[name].update(config_dict)

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

    def get_data_chef(self, name: str) -> Dict[str, Any]:
        """
        Get a specific data chef configuration.

        :param name:
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

        return config_dict[name]
