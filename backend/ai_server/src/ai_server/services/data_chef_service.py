from enum import Enum
from typing import Any
from omegaconf import DictConfig
from sqlalchemy import text
from ..services.database_service import DatabaseService


class DataType(str, Enum):
    SQL = "sql"
    NOSQL = "nosql"
    CSV = "csv"
    API = "api"
    CUSTOM = "custom"


def _cook_sql(query: str) -> Any:
    """
    :param query: SQL query string to execute.
    :return:
    Generator yielding rows from the SQL query result.
    Raises ValueError if the query execution fails.
    """
    service = DatabaseService().get_sql()
    try:
        with service.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(text(query))
            while True:
                chunk = list(result.fetchmany(1000))
                if not chunk:
                    break
                yield from chunk
    except Exception as e:
        raise ValueError(f"An error occurred while querying the SQL database: {e}")


def _cook_nosql(database: str, collection: str) -> Any:
    """
    Query a NoSQL database and yield results in chunks.
    :param database:
    :param collection:
    :return:
    Generator yielding documents from the NoSQL collection.
    Raises ValueError if the collection is not found or if an error occurs.
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
            yield from chunk
            skip_count += batch_size
    except Exception as e:
        raise ValueError(f"An error occurred while querying the NoSQL database: {e}")


def _cook_csv(path: str) -> Any:
    import pandas as pd
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        raise ValueError(f"CSV file not found at path: {path}")
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty or invalid.")
    except Exception as e:
        raise ValueError(f"An error occurred while reading the CSV file: {e}")


def _cook_api(url: str) -> Any:
    import requests
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # Assuming the API returns JSON data
    except requests.RequestException as e:
        raise ValueError(f"API request failed: {e}")
    except ValueError:
        raise ValueError("Invalid JSON response from API")


class DataChefService:

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        pass

    def cook(self, name: str) -> Any:
        data = self.cfg.get(name, None)
        if data is None:
            raise ValueError(f"Configuration for {name} not found in DataChefService")

        try:
            type_enum = DataType(data.type.lower())
        except ValueError:
            raise ValueError(
                f"Invalid data type: {data.type}. Must be one of {[t.value for t in DataType]}."
            )

        if type_enum == DataType.SQL:
            query_str = str(data.query)
            return _cook_sql(query_str)
        elif type_enum == DataType.NOSQL:
            db_name = str(data.database)
            collection_name = str(data.collection)
            return _cook_nosql(db_name, collection_name)
        elif type_enum == DataType.CSV:
            path_str = str(data.path)
            return _cook_csv(path_str)
        elif type_enum == DataType.API:
            url_str = str(data.url)
            return _cook_api(url_str)
        else:
            raise NotImplementedError(f"Data type {type_enum} is not implemented.")
