import hydra
from omegaconf import DictConfig
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.pool import QueuePool
from typing import Any


class CustomQueuePool(QueuePool):
    def __init__(self, *args, **kwargs):
        self.conn_max_idle_time = kwargs.pop('conn_max_idle_time', None)
        super().__init__(*args, **kwargs)


class DatabaseService:

    def get_database_specific_args(self, db_type, ssl, conn_max_idle_time):
        """Return database-specific connection arguments"""
        args = {}

        if db_type.lower() == 'postgresql':
            if ssl:
                args['sslmode'] = 'require'
            args['connect_timeout'] = 30

        elif db_type.lower() == 'mysql':
            if ssl:
                args['ssl_disabled'] = False
            args['read_timeout'] = conn_max_idle_time
            args['write_timeout'] = conn_max_idle_time
            args['connect_timeout'] = 30

        elif db_type.lower() == 'sqlite':
            args['timeout'] = conn_max_idle_time

        return args

    def build_connection_string(self, db_type, host, port, user, password, database, ssl):
        """Build connection string with SSL support"""
        if db_type.lower() == 'postgresql':
            ssl_param = '?sslmode=require' if ssl else ''
            return f"postgresql://{user}:{password}@{host}:{port}/{database}{ssl_param}"
        elif db_type.lower() == 'mysql':
            ssl_param = '?ssl=true' if ssl else ''
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}{ssl_param}"
        elif db_type.lower() == 'sqlite':
            return f"sqlite:///{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @hydra.main(config_path="../config", config_name="local", version_base=None)
    def get_sql(self, cfg: DictConfig) -> Engine:
        """
        Returns the database instance using ALL config parameters.
        """
        # Extract ALL parameters from config
        db_type = cfg.database.sql.type
        host = cfg.database.sql.host
        port = cfg.database.sql.port
        user = cfg.database.sql.user
        password = cfg.database.sql.password
        database = cfg.database.sql.database
        ssl = cfg.database.sql.ssl
        max_idle_conns = cfg.database.sql.max_idle_conns
        max_open_conns = cfg.database.sql.max_open_conns
        conn_max_lifetime = cfg.database.sql.conn_max_lifetime
        conn_max_idle_time = cfg.database.sql.conn_max_idle_time

        # Build connection string with SSL parameter
        connection_string = self.build_connection_string(
            db_type, host, port, user, password, database, ssl
        )

        # Create engine using ALL config parameters
        engine = create_engine(
            connection_string,
            # Pool configuration using ALL parameters
            poolclass=CustomQueuePool,
            pool_size=max_idle_conns,
            max_overflow=max_open_conns - max_idle_conns,
            pool_timeout=30,
            pool_recycle=conn_max_lifetime,
            pool_pre_ping=True,
            pool_use_lifo=True,
            pool_reset_on_return='rollback',

            # Pass conn_max_idle_time to custom pool
            conn_max_idle_time=conn_max_idle_time,

            # Database-specific connection arguments
            connect_args=self.get_database_specific_args(db_type, ssl, conn_max_idle_time),

            # Execution options
            execution_options={
                'autocommit': False,
                'isolation_level': 'READ_COMMITTED'
            }
        )

        # Event listener for additional connection setup if needed
        @event.listens_for(engine, "connect")
        def set_connection_settings(dbapi_connection, connection_record):
            """Set connection-level settings"""
            pass

        return engine

    def build_mongodb_connection_string(self, host, port, username, password, ssl, auth_source, replica_set):
        """Build MongoDB connection string with all parameters"""
        # Basic connection string
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}"
        else:
            connection_string = f"mongodb://{host}:{port}"

        # Add query parameters
        params = []
        if auth_source:
            params.append(f"authSource={auth_source}")
        if replica_set:
            params.append(f"replicaSet={replica_set}")
        if ssl:
            params.append("ssl=true")

        if params:
            connection_string += "?" + "&".join(params)

        return connection_string

    @hydra.main(config_path="../config", config_name="local", version_base=None)
    def get_nosql(self, cfg: DictConfig) -> Any:
        """
        Returns the NoSQL database instance using ALL config parameters.
        """
        db_type = cfg.database.nosql.type
        if db_type != "mongodb":
            raise NotImplementedError("This method should be overridden by subclasses.")

        # Extract ALL NoSQL config parameters
        host = cfg.database.nosql.host
        port = cfg.database.nosql.port
        username = cfg.database.nosql.username
        password = cfg.database.nosql.password
        ssl = cfg.database.nosql.ssl
        max_idle_conns = cfg.database.nosql.max_idle_conns
        max_open_conns = cfg.database.nosql.max_open_conns
        conn_max_lifetime = cfg.database.nosql.conn_max_lifetime
        conn_max_idle_time = cfg.database.nosql.conn_max_idle_time
        connection_timeout = cfg.database.nosql.connection_timeout
        auth_source = cfg.database.nosql.auth_source
        replica_set = cfg.database.nosql.replica_set
        server_selection_timeout = cfg.database.nosql.server_selection_timeout

        # Build MongoDB connection string
        connection_string = self.build_mongodb_connection_string(
            host, port, username, password, ssl, auth_source, replica_set
        )

        # Convert string timeouts to milliseconds for MongoDB
        def parse_timeout(timeout_str):
            if timeout_str.endswith('s'):
                return int(timeout_str[:-1]) * 1000
            elif timeout_str.endswith('ms'):
                return int(timeout_str[:-2])
            return int(timeout_str) * 1000

        connection_timeout_ms = parse_timeout(connection_timeout)
        server_selection_timeout_ms = parse_timeout(server_selection_timeout)
        conn_max_lifetime_ms = parse_timeout(conn_max_lifetime)
        conn_max_idle_time_ms = parse_timeout(conn_max_idle_time)

        # MongoDB client options using ALL parameters
        client_options = {
            'connectTimeoutMS': connection_timeout_ms,
            'serverSelectionTimeoutMS': server_selection_timeout_ms,
            'maxPoolSize': max_open_conns,
            'minPoolSize': max_idle_conns,
            'maxIdleTimeMS': conn_max_idle_time_ms,
            'maxConnecting': max_open_conns,
            'ssl': ssl,
        }

        # Add a replica set if specified
        if replica_set:
            client_options['replicaSet'] = replica_set

        # Add an auth source if specified
        if auth_source:
            client_options['authSource'] = auth_source

        # Create MongoDB client (assuming pymongo)
        try:
            from pymongo import MongoClient
            client = MongoClient(connection_string, **client_options)
            return client
        except ImportError:
            raise ImportError("pymongo is required for MongoDB connections. Install with: pip install pymongo")
