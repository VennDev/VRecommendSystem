import loguru
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from urllib.parse import quote_plus
from sqlalchemy import create_engine, Engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Base for ORM models
Base = declarative_base()


class DatabaseConfig:
    """Database configuration class."""

    def __init__(
            self,
            host: str,
            port: int,
            database: str,
            username: str,
            password: str,
            db_type: str = "mysql",
            ssl: Optional[bool] = False,
            max_idle_conns: Optional[int] = 10,
            max_open_conns: Optional[int] = 100,
            conn_max_lifetime: Optional[str] = "30s",
            conn_max_idle_time: Optional[str] = "30s",
    ) -> None:
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.db_type = db_type.lower()
        self.ssl = ssl
        self.max_idle_conns = max_idle_conns
        self.max_open_conns = max_open_conns
        self.conn_max_lifetime = conn_max_lifetime
        self.conn_max_idle_time = conn_max_idle_time

        if self.db_type not in ["postgresql", "mysql"]:
            raise ValueError("db_type must be 'postgresql' or 'mysql'")

    def _parse_time_duration(self, duration: str) -> int:
        """Parse time duration string to seconds."""
        if duration.endswith("s"):
            return int(duration[:-1])
        elif duration.endswith("m"):
            return int(duration[:-1]) * 60
        elif duration.endswith("h"):
            return int(duration[:-1]) * 3600
        else:
            return int(duration)  # assume seconds if no unit


class SQLDatabase:
    """SQL Database connection and operations class."""

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker[Session]] = None
        self._connection_string = self._build_connection_string()

    def _build_connection_string(self) -> str:
        """Build database connection string."""
        encoded_password = quote_plus(self.config.password)
        encoded_username = quote_plus(self.config.username)

        if self.config.db_type == "postgresql":
            driver = "postgresql+psycopg2"
            ssl_param = "?sslmode=require" if self.config.ssl else ""
        elif self.config.db_type == "mysql":
            driver = "mysql+pymysql"
            ssl_param = "?ssl=true" if self.config.ssl else ""
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

        base_url = (
            f"{driver}://{encoded_username}:{encoded_password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )

        return f"{base_url}{ssl_param}"

    def connect(self) -> None:
        """Establish database connection."""
        try:
            # Convert time duration strings to seconds
            pool_recycle = self.config._parse_time_duration(
                self.config.conn_max_lifetime
            )
            pool_timeout = self.config._parse_time_duration(
                self.config.conn_max_idle_time
            )

            # Create engine with configuration parameters
            engine_kwargs = {
                "poolclass": QueuePool,
                "pool_size": self.config.max_idle_conns,
                "max_overflow": self.config.max_open_conns - self.config.max_idle_conns,
                "pool_pre_ping": True,
                "pool_recycle": pool_recycle,
                "pool_timeout": pool_timeout,
                "echo": False,
            }

            # Add SSL-specific parameters if needed
            if self.config.ssl:
                if self.config.db_type == "postgresql":
                    engine_kwargs["connect_args"] = {"sslmode": "require"}
                elif self.config.db_type == "mysql":
                    engine_kwargs["connect_args"] = {"ssl_disabled": False}

            self.engine = create_engine(self._connection_string, **engine_kwargs)
            self.session_factory = sessionmaker(bind=self.engine)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            loguru.logger.info(
                f"Successfully connected to {self.config.db_type} database with SSL: {self.config.ssl}"
            )
            loguru.logger.info(
                f"Connection pool config - Max idle: {self.config.max_idle_conns}, "
                f"Max open: {self.config.max_open_conns}, "
                f"Max lifetime: {self.config.conn_max_lifetime}, "
                f"Max idle time: {self.config.conn_max_idle_time}"
            )

        except SQLAlchemyError as e:
            loguru.logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.session_factory = None
            loguru.logger.info("Database connection closed")

    @contextmanager
    def get_session(self):
        """Get database session with context manager."""
        if not self.session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")

        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            loguru.logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def execute_query(
            self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results."""
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), parameters or {})
                columns = result.keys()
                rows = result.fetchall()

                return [dict(zip(columns, row)) for row in rows]

        except SQLAlchemyError as e:
            loguru.logger.error(f"Query execution failed: {e}")
            raise

    def execute_non_query(
            self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Execute INSERT, UPDATE, DELETE query and return affected rows."""
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(text(query), parameters or {})
                    return result.rowcount

        except SQLAlchemyError as e:
            loguru.logger.error(f"Non-query execution failed: {e}")
            raise

    def insert_record(self, table_name: str, data: Dict[str, Any]) -> Optional[int]:
        """Insert a single record and return the ID if applicable."""
        if not data:
            raise ValueError("Data cannot be empty")

        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())

        if self.config.db_type == "postgresql":
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING id"
        else:  # MySQL
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        try:
            if self.config.db_type == "postgresql":
                result = self.execute_query(query, data)
                return result[0]["id"] if result else None
            else:
                self.execute_non_query(query, data)
                # For MySQL, get last insert ID
                last_id_result = self.execute_query("SELECT LAST_INSERT_ID() as id")
                return last_id_result[0]["id"] if last_id_result else None

        except SQLAlchemyError as e:
            loguru.logger.error(f"Insert failed: {e}")
            raise

    def update_record(
            self,
            table_name: str,
            data: Dict[str, Any],
            condition: str,
            condition_params: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Update records based on condition."""
        if not data:
            raise ValueError("Data cannot be empty")

        set_clause = ", ".join(f"{key} = :{key}" for key in data.keys())
        query = f"UPDATE {table_name} SET {set_clause} WHERE {condition}"

        # Combine data and condition parameters
        all_params = data.copy()
        if condition_params:
            all_params.update(condition_params)

        return self.execute_non_query(query, all_params)

    def delete_record(
            self,
            table_name: str,
            condition: str,
            condition_params: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Delete records based on condition."""
        query = f"DELETE FROM {table_name} WHERE {condition}"
        return self.execute_non_query(query, condition_params or {})

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table structure information."""
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")

        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)

        return [
            {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col["nullable"],
                "default": col["default"],
            }
            for col in columns
        ]

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")

        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def create_table_from_dict(
            self, table_name: str, columns_def: Dict[str, str]
    ) -> None:
        """Create table from column definitions dictionary."""
        if not columns_def:
            raise ValueError("Columns definition cannot be empty")

        columns_sql = []
        for col_name, col_type in columns_def.items():
            columns_sql.append(f"{col_name} {col_type}")

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns_sql)})"
        self.execute_non_query(query)

    def bulk_insert(self, table_name: str, data_list: List[Dict[str, Any]]) -> int:
        """Bulk insert multiple records."""
        if not data_list:
            return 0

        # Assume all dictionaries have the same keys
        columns = list(data_list[0].keys())
        columns_str = ", ".join(columns)
        placeholders = ", ".join(f":{key}" for key in columns)

        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        try:
            with self.get_session() as session:
                result = session.execute(text(query), data_list)
                return result.rowcount

        except SQLAlchemyError as e:
            loguru.logger.error(f"Bulk insert failed: {e}")
            raise

    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "username": self.config.username,
            "db_type": self.config.db_type,
            "ssl": self.config.ssl,
            "max_idle_conns": self.config.max_idle_conns,
            "max_open_conns": self.config.max_open_conns,
            "conn_max_lifetime": self.config.conn_max_lifetime,
            "conn_max_idle_time": self.config.conn_max_idle_time,
            "connected": self.engine is not None,
        }
