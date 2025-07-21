import os
from dataclasses import dataclass

@dataclass
class SparkConfigResult:
    spark_master: str
    spark_app_name: str

def get_spark_config() -> SparkConfigResult:
    return SparkConfigResult(
        spark_master=os.getenv("SPARK_MASTER", "local[*]"),
        spark_app_name=os.getenv("SPARK_APP_NAME", "MySparkApp")
    )

