from sqlalchemy import create_engine
from ...interfaces.iprovider import IProvider
from ...configs.database_config import get_database_config
from ...utils import connection_url_builder
from sqlalchemy.engine import Connection

class SQL(IProvider):

    def connect(self) -> "Connection":
        cfg = get_database_config() 
        url = connection_url_builder.build_connection_url(cfg.database_type) 
        connection = create_engine(
            url,
            pool_size=cfg.database_max_open_conns,
            max_overflow=cfg.database_max_idle_conns,
            pool_recycle=int(cfg.database_conn_max_lifetime),
            pool_timeout=int(cfg.database_conn_max_idle_time),
        )
        return connection.connect() 
