from typing import Any, Dict, List, Optional, Union, Tuple, MutableMapping
from contextlib import contextmanager
from datetime import datetime

import loguru
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError, ConnectionFailure, DuplicateKeyError
from pymongo.results import (
    InsertOneResult,
    InsertManyResult,
    UpdateResult,
    DeleteResult,
)


class MongoConfig:
    """MongoDB configuration class."""

    def __init__(
            self,
            host: str = "localhost",
            port: int = 27017,
            database: str = "test",
            username: Optional[str] = None,
            password: Optional[str] = None,
            auth_source: str = "admin",
            replica_set: Optional[str] = None,
            ssl: Optional[bool] = False,
            max_idle_conns: Optional[int] = 10,
            max_open_conns: Optional[int] = 100,
            conn_max_lifetime: Optional[str] = "30s",
            conn_max_idle_time: Optional[str] = "30s",
            connection_timeout: int = 5000,
            server_selection_timeout: int = 5000,
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.auth_source = auth_source
        self.replica_set = replica_set
        self.ssl = ssl
        self.max_idle_conns = max_idle_conns
        self.max_open_conns = max_open_conns
        self.conn_max_lifetime = conn_max_lifetime
        self.conn_max_idle_time = conn_max_idle_time
        self.connection_timeout = connection_timeout
        self.server_selection_timeout = server_selection_timeout

    def _parse_time_duration(self, duration: str) -> int:
        """Parse time duration string to milliseconds."""
        if duration.endswith("s"):
            return int(duration[:-1]) * 1000
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60 * 1000
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600 * 1000
        else:
            return int(duration) * 1000  # assume seconds if no unit


class NoSQLDatabase:
    """MongoDB connection and operations class."""

    def __init__(self, config: MongoConfig) -> None:
        self.config = config
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._connection_string = self._build_connection_string()

    def _build_connection_string(self) -> str:
        """Build MongoDB connection string."""
        if self.config.username and self.config.password:
            auth_part = f"{self.config.username}:{self.config.password}@"
        else:
            auth_part = ""

        connection_params = []

        if self.config.auth_source:
            connection_params.append(f"authSource={self.config.auth_source}")

        if self.config.replica_set:
            connection_params.append(f"replicaSet={self.config.replica_set}")

        if self.config.ssl:
            connection_params.append("ssl=true")

        # Add connection pool parameters
        connection_params.append(f"maxPoolSize={self.config.max_open_conns}")
        connection_params.append(f"minPoolSize={self.config.max_idle_conns}")

        # Convert time durations to milliseconds
        max_idle_time_ms = self.config._parse_time_duration(
            self.config.conn_max_idle_time
        )
        max_lifetime_ms = self.config._parse_time_duration(
            self.config.conn_max_lifetime
        )

        connection_params.append(f"maxIdleTimeMS={max_idle_time_ms}")
        connection_params.append(f"maxConnectingTimeMS={max_lifetime_ms}")

        # Existing timeout parameters
        connection_params.append(f"connectTimeoutMS={self.config.connection_timeout}")
        connection_params.append(
            f"serverSelectionTimeoutMS={self.config.server_selection_timeout}"
        )

        params_string = "&".join(connection_params)

        return (
            f"mongodb://{auth_part}{self.config.host}:{self.config.port}/"
            f"{self.config.database}?{params_string}"
        )

    def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            # Create client options dictionary
            client_options = {
                "maxPoolSize": self.config.max_open_conns,
                "minPoolSize": self.config.max_idle_conns,
                "maxIdleTimeMS": self.config._parse_time_duration(
                    self.config.conn_max_idle_time
                ),
                "connectTimeoutMS": self.config.connection_timeout,
                "serverSelectionTimeoutMS": self.config.server_selection_timeout,
            }

            # Add SSL options if enabled
            if self.config.ssl:
                client_options["ssl"] = True

            # Add authentication options if provided
            if self.config.username and self.config.password:
                client_options["username"] = self.config.username
                client_options["password"] = self.config.password
                client_options["authSource"] = self.config.auth_source

            # Add a replica set if specified
            if self.config.replica_set:
                client_options["replicaSet"] = self.config.replica_set

            self.client = MongoClient(
                f"mongodb://{self.config.host}:{self.config.port}/", **client_options
            )

            self.database = self.client[self.config.database]

            # Test connection
            self.client.admin.command("ping")

            loguru.logger.info(
                f"Successfully connected to MongoDB database: {self.config.database}"
            )
            loguru.logger.info(
                f"Connection config - SSL: {self.config.ssl}, "
                f"Max idle: {self.config.max_idle_conns}, "
                f"Max open: {self.config.max_open_conns}, "
                f"Max lifetime: {self.config.conn_max_lifetime}, "
                f"Max idle time: {self.config.conn_max_idle_time}"
            )

        except ConnectionFailure as e:
            loguru.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except PyMongoError as e:
            loguru.logger.error(f"MongoDB error: {e}")
            raise

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            loguru.logger.info("MongoDB connection closed")

    def get_collection(self, collection_name: str) -> Collection:
        """Get MongoDB collection."""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")

        return self.database[collection_name]

    @contextmanager
    def get_session(self):
        """Get MongoDB session with context manager for transactions."""
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self.client.start_session()
        try:
            yield session
        except Exception as e:
            loguru.logger.error(f"Session error: {e}")
            raise
        finally:
            session.end_session()

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document and return the ObjectId as string."""
        if not document:
            raise ValueError("Document cannot be empty")

        try:
            collection = self.get_collection(collection_name)

            # Add timestamp if not exists
            if "created_at" not in document:
                document["created_at"] = datetime.utcnow()

            result: InsertOneResult = collection.insert_one(document)

            loguru.logger.info(f"Inserted document with ID: {result.inserted_id}")
            return str(result.inserted_id)

        except DuplicateKeyError as e:
            loguru.logger.error(f"Duplicate key error: {e}")
            raise
        except PyMongoError as e:
            loguru.logger.error(f"Insert failed: {e}")
            raise

    def insert_many(
            self, collection_name: str, documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert multiple documents and return list of ObjectIds as strings."""
        if not documents:
            return []

        try:
            collection = self.get_collection(collection_name)

            # Add timestamps
            for doc in documents:
                if "created_at" not in doc:
                    doc["created_at"] = datetime.utcnow()

            result: InsertManyResult = collection.insert_many(documents)

            inserted_ids = [str(obj_id) for obj_id in result.inserted_ids]
            loguru.logger.info(f"Inserted {len(inserted_ids)} documents")

            return inserted_ids

        except PyMongoError as e:
            loguru.logger.error(f"Bulk insert failed: {e}")
            raise

    def find_one(
            self,
            collection_name: str,
            filter_dict: Optional[Dict[str, Any]] = None,
            projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        try:
            collection = self.get_collection(collection_name)

            # Convert string ObjectId to ObjectId object if needed
            if filter_dict and "_id" in filter_dict:
                if isinstance(filter_dict["_id"], str):
                    filter_dict["_id"] = ObjectId(filter_dict["_id"])

            result = collection.find_one(filter_dict or {}, projection)

            # Convert ObjectId to string for JSON serialization
            if result and "_id" in result:
                result["_id"] = str(result["_id"])

            return result

        except PyMongoError as e:
            loguru.logger.error(f"Find one failed: {e}")
            raise

    def find_many(
            self,
            collection_name: str,
            filter_dict: Optional[Dict[str, Any]] = None,
            projection: Optional[Dict[str, Any]] = None,
            sort: Optional[List[Tuple[str, int]]] = None,
            limit: Optional[int] = None,
            skip: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find multiple documents with optional sorting, limiting, and skipping."""
        try:
            collection = self.get_collection(collection_name)

            # Convert string ObjectId to ObjectId object if needed
            if filter_dict and "_id" in filter_dict:
                if isinstance(filter_dict["_id"], str):
                    filter_dict["_id"] = ObjectId(filter_dict["_id"])

            cursor = collection.find(filter_dict or {}, projection)

            if sort:
                cursor = cursor.sort(sort)

            if skip:
                cursor = cursor.skip(skip)

            if limit:
                cursor = cursor.limit(limit)

            results = list(cursor)

            # Convert ObjectIds to strings for JSON serialization
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            return results

        except PyMongoError as e:
            loguru.logger.error(f"Find many failed: {e}")
            raise

    def update_one(
            self,
            collection_name: str,
            filter_dict: Dict[str, Any],
            update_doc: Dict[str, Any],
            upsert: bool = False,
    ) -> int:
        """Update a single document."""
        if not filter_dict or not update_doc:
            raise ValueError("Filter and update document cannot be empty")

        try:
            collection = self.get_collection(collection_name)

            # Convert string ObjectId to ObjectId object if needed
            if "_id" in filter_dict and isinstance(filter_dict["_id"], str):
                filter_dict["_id"] = ObjectId(filter_dict["_id"])

            # Add update timestamp
            if "$set" not in update_doc:
                update_doc = {"$set": update_doc}

            if "updated_at" not in update_doc.get("$set", {}):
                update_doc["$set"]["updated_at"] = datetime.utcnow()

            result: UpdateResult = collection.update_one(
                filter_dict, update_doc, upsert=upsert
            )

            loguru.logger.info(f"Updated {result.modified_count} document(s)")
            return result.modified_count

        except PyMongoError as e:
            loguru.logger.error(f"Update one failed: {e}")
            raise

    def update_many(
            self,
            collection_name: str,
            filter_dict: Dict[str, Any],
            update_doc: Dict[str, Any],
            upsert: bool = False,
    ) -> int:
        """Update multiple documents."""
        if not filter_dict or not update_doc:
            raise ValueError("Filter and update document cannot be empty")

        try:
            collection = self.get_collection(collection_name)

            # Add update timestamp
            if "$set" not in update_doc:
                update_doc = {"$set": update_doc}

            if "updated_at" not in update_doc.get("$set", {}):
                update_doc["$set"]["updated_at"] = datetime.utcnow()

            result: UpdateResult = collection.update_many(
                filter_dict, update_doc, upsert=upsert
            )

            loguru.logger.info(f"Updated {result.modified_count} document(s)")
            return result.modified_count

        except PyMongoError as e:
            loguru.logger.error(f"Update many failed: {e}")
            raise

    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete a single document."""
        if not filter_dict:
            raise ValueError("Filter cannot be empty")

        try:
            collection = self.get_collection(collection_name)

            # Convert string ObjectId to ObjectId object if needed
            if "_id" in filter_dict and isinstance(filter_dict["_id"], str):
                filter_dict["_id"] = ObjectId(filter_dict["_id"])

            result: DeleteResult = collection.delete_one(filter_dict)

            loguru.logger.info(f"Deleted {result.deleted_count} document(s)")
            return result.deleted_count

        except PyMongoError as e:
            loguru.logger.error(f"Delete one failed: {e}")
            raise

    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        if not filter_dict:
            raise ValueError("Filter cannot be empty")

        try:
            collection = self.get_collection(collection_name)

            result: DeleteResult = collection.delete_many(filter_dict)

            loguru.logger.info(f"Deleted {result.deleted_count} document(s)")
            return result.deleted_count

        except PyMongoError as e:
            loguru.logger.error(f"Delete many failed: {e}")
            raise

    def count_documents(
            self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count documents in a collection."""
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {})

        except PyMongoError as e:
            loguru.logger.error(f"Count documents failed: {e}")
            raise

    def create_index(
            self,
            collection_name: str,
            index_spec: Union[str, List[Tuple[str, int]]],
            unique: bool = False,
            background: bool = True,
    ) -> str:
        """Create an index on collection."""
        try:
            collection = self.get_collection(collection_name)

            index_name = collection.create_index(
                index_spec, unique=unique, background=background
            )

            loguru.logger.info(f"Created index: {index_name}")
            return index_name

        except PyMongoError as e:
            loguru.logger.error(f"Create index failed: {e}")
            raise

    def drop_index(self, collection_name: str, index_name: str) -> None:
        """Drop an index from collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.drop_index(index_name)

            loguru.logger.info(f"Dropped index: {index_name}")

        except PyMongoError as e:
            loguru.logger.error(f"Drop index failed: {e}")
            raise

    def list_indexes(self, collection_name: str) -> list[MutableMapping[str, Any]]:
        """List all indexes in collection."""
        try:
            collection = self.get_collection(collection_name)
            return list(collection.list_indexes())

        except PyMongoError as e:
            loguru.logger.error(f"List indexes failed: {e}")
            raise

    def drop_collection(self, collection_name: str) -> None:
        """Drop a collection."""
        try:
            collection = self.get_collection(collection_name)
            collection.drop()

            loguru.logger.info(f"Dropped collection: {collection_name}")

        except PyMongoError as e:
            loguru.logger.error(f"Drop collection failed: {e}")
            raise

    def list_collections(self) -> List[str]:
        """List all collections in database."""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            return self.database.list_collection_names()

        except PyMongoError as e:
            loguru.logger.error(f"List collections failed: {e}")
            raise

    def aggregate(
            self, collection_name: str, pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Perform an aggregation query."""
        try:
            collection = self.get_collection(collection_name)

            cursor = collection.aggregate(pipeline)
            results = list(cursor)

            # Convert ObjectIds to strings
            for doc in results:
                if "_id" in doc and isinstance(doc["_id"], ObjectId):
                    doc["_id"] = str(doc["_id"])

            return results

        except PyMongoError as e:
            loguru.logger.error(f"Aggregation failed: {e}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            stats = self.database.command("dbstats")
            return dict(stats)

        except PyMongoError as e:
            loguru.logger.error(f"Get database stats failed: {e}")
            raise

    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "username": self.config.username,
            "ssl": self.config.ssl,
            "max_idle_conns": self.config.max_idle_conns,
            "max_open_conns": self.config.max_open_conns,
            "conn_max_lifetime": self.config.conn_max_lifetime,
            "conn_max_idle_time": self.config.conn_max_idle_time,
            "connected": self.client is not None,
        }
