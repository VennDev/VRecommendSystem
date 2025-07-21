from ...interfaces.iprovider import IProvider
from ...utils import connection_url_builder
from ...configs.spark_config import get_spark_config
from pyspark.sql import SparkSession

class Spark(IProvider):
    def connect(self) -> "SparkSession":
        cfg = get_spark_config()
        spark_url = connection_url_builder.build_connection_url("spark")
        from pyspark.sql import SparkSession

        spark = SparkSession.builder \
            .master(spark_url) \
            .appName(cfg.spark_app_name) \
            .getOrCreate()

        return spark

