import redis
from ...interfaces.iprovider import IProvider
from ...configs.redis_config import get_redis_config
from ...utils import connection_url_builder


class Redis(IProvider):

    def connect(self):
        cfg = get_redis_config()
        redis_url = connection_url_builder.build_connection_url("redis")
        redis_client = redis.from_url(
            redis_url, ssl=cfg.redis_ssl, decode_responses=cfg.redis_decode
        )
        return redis_client
