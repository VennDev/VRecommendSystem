import os
from dataclasses import dataclass

@dataclass
class DataBaseConfigResult:
    database_type: str
    database_host: str
    database_port: int
    database_user: str
    database_password: str
    database_name: str
    database_ssl_mode: str
    database_max_open_conns: int
    database_max_idle_conns: int
    database_conn_max_lifetime: str
    database_conn_max_idle_time: str

def get_database_config() -> DataBaseConfigResult:
    return DataBaseConfigResult(
        database_type=os.getenv("DATABASE_TYPE", "mysql"),
        database_host=os.getenv("DATABASE_HOST", "localhost"),
        database_port=int(os.getenv("DATABASE_PORT", 3306)),
        database_user=os.getenv("DATABASE_USER", "root"),
        database_password=os.getenv("DATABASE_PASSWORD", "password"),
        database_name=os.getenv("DATABASE_NAME", "api_server_db"),
        database_ssl_mode=os.getenv("DATABASE_SSL_MODE", "prefer"),
        database_max_open_conns=int(os.getenv("DATABASE_MAX_OPEN_CONNS", 100)),
        database_max_idle_conns=int(os.getenv("DATABASE_MAX_IDLE_CONNS", 10)),
        database_conn_max_lifetime=os.getenv("DATABASE_CONN_MAX_LIFETIME", "30"),
        database_conn_max_idle_time=os.getenv("DATABASE_CONN_MAX_IDLE_TIME", "30")
    )