import os
from dataclasses import dataclass

@dataclass
class RedisConfigResult:
    redis_host: str
    redis_port: int
    redis_db: int
    redis_username: str
    reids_password: str
    redis_ssl: bool
    redis_decode: bool
    
def get_redis_config() -> RedisConfigResult:
    return RedisConfigResult(
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", 3306)),
        redis_db=int(os.getenv("REDIS_DB", 0)),
        redis_username=os.getenv("REDIS_USERNAME", "default"),
        redis_password=os.getenv("REDIS_PASSWORD", "password"),
        redis_ssl=os.getenv("REDIS_SSL", "false").lower() == "true",
        redis_decode=os.getenv("REDIS_DECODE", "false").lower() == "true"
    )