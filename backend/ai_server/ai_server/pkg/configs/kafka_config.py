import os
from dataclasses import dataclass

@dataclass
class KafkaConfigResult:
    kafka_bootstrap_servers: list 
    kafka_topics: list 

def get_kafka_config() -> KafkaConfigResult:
    return KafkaConfigResult(
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(","),
        kafka_topics=os.getenv("KAFKA_TOPICS", "topic1,topic2").split(",")
    )
