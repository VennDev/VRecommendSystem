from typing import Optional, Tuple
from pyspark.sql import SparkSession
from loguru import logger
from confluent_kafka import Consumer, Producer
from .providers.sql import SQL as SQLProvider 
from .providers.kafka import Kafka as KafkaProvider
from .providers.redis import Redis as RedisProvider
from .providers.spark import Spark as SparkProvider

class ConnectionManager:

    def __init__(self):
        self._kafka_connections: Optional[Tuple[Consumer, Producer]] = None
        self._redis_connection = None
        self._spark_connection: Optional[SparkSession] = None
        self._sql_connection = None
        
        # Initialize providers
        self.kafka_provider = KafkaProvider()
        self.redis_provider = RedisProvider()
        self.spark_provider = SparkProvider()
        self.sql_provider = SQLProvider()
    
    def get_kafka_connections(self) -> Tuple[Consumer, Producer]:
        """Get Kafka consumer and producer"""
        if self._kafka_connections is None:
            try:
                self._kafka_connections = self.kafka_provider.connect()
                logger.info("Kafka connections established")
            except Exception as e:
                logger.error(f"Failed to establish Kafka connections: {e}")
                raise
        return self._kafka_connections
    
    def get_redis_connection(self):
        """Get Redis connection"""
        if self._redis_connection is None:
            try:
                self._redis_connection = self.redis_provider.connect()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to establish Redis connection: {e}")
                raise
        return self._redis_connection
    
    def get_spark_connection(self) -> SparkSession:
        """Get Spark session"""
        if self._spark_connection is None:
            try:
                self._spark_connection = self.spark_provider.connect()
                logger.info("Spark connection established")
            except Exception as e:
                logger.error(f"Failed to establish Spark connection: {e}")
                raise
        return self._spark_connection
    
    def get_sql_connection(self):
        """Get SQL connection"""
        if self._sql_connection is None:
            try:
                self._sql_connection = self.sql_provider.connect()
                logger.info("SQL connection established")
            except Exception as e:
                logger.error(f"Failed to establish SQL connection: {e}")
                raise
        return self._sql_connection
    
    def close_all_connections(self):
        """Close all connections"""
        try:
            if self._kafka_connections:
                consumer, producer = self._kafka_connections
                consumer.close()
                producer.flush()
                producer.close()
            
            if self._redis_connection:
                self._redis_connection.close()
            
            if self._spark_connection:
                self._spark_connection.stop()
                
            if self._sql_connection:
                self._sql_connection.close()
                
            logger.info("All connections closed successfully")
        except Exception as e:
            logger.error(f"Error closing connections: {e}")
