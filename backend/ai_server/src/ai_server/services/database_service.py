import hydra
from omegaconf import DictConfig
from typing import Union
from ..database.nosql import MongoConfig, NoSQLDatabase
from ..database.sql import SQLDatabase, DatabaseConfig


class DatabaseService:

    @hydra.main(config_path="../config", config_name="local", version_base=None)
    def get_database(self, cfg: DictConfig) -> Union[NoSQLDatabase, SQLDatabase]:
        """
        Returns the database instance.
        """
        db_type = cfg.database.type
        if db_type == "mongodb":
            db_cfg = MongoConfig(
                host=cfg.database.host,
                port=cfg.database.port,
                database=cfg.database.name,
                username=cfg.database.username,
                password=cfg.database.password,
                auth_source=cfg.database.auth_source,
                replica_set=cfg.database.replica_set,
                ssl=cfg.database.ssl,
                max_idle_conns=cfg.database.max_idle_conns,
                max_open_conns=cfg.database.max_open_conns,
                conn_max_lifetime=cfg.database.conn_max_lifetime,
                conn_max_idle_time=cfg.database.conn_max_idle_time,
                connection_timeout=cfg.database.connection_timeout,
                server_selection_timeout=cfg.database.server_selection_timeout,
            )
            return NoSQLDatabase(config=db_cfg)
        elif db_type == "postgresql" or db_type == "mysql":
            db_cfg = DatabaseConfig(
                host=cfg.database.host,
                port=cfg.database.port,
                database=cfg.database.name,
                username=cfg.database.username,
                password=cfg.database.password,
                db_type=db_type,
                ssl=cfg.database.ssl,
                max_idle_conns=cfg.database.max_idle_conns,
                max_open_conns=cfg.database.max_open_conns,
                conn_max_lifetime=cfg.database.conn_max_lifetime,
                conn_max_idle_time=cfg.database.conn_max_idle_time,
            )
            return SQLDatabase(config=db_cfg)
        raise NotImplementedError("This method should be overridden by subclasses.")
