import json
import logging
from typing import List, Dict, Any, Optional, Callable
from confluent_kafka import Consumer as KafkaConsumer, KafkaError, KafkaException
from omegaconf import DictConfig
import signal
from threading import Event


class Consumer:
    """
    Kafka KafkaConsumer wrapper using confluent_kafka library
    Optimized for AI server consumer-only operations
    """

    def __init__(self, cfg: DictConfig):
        self.cfg = cfg
        self.logger = logging.getLogger(__name__)
        self.consumer: Optional[KafkaConsumer] = None
        self.running = Event()
        self.message_handler: Optional[Callable] = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _build_consumer_config(self) -> Dict[str, Any]:
        """Build consumer configuration from Hydra config"""
        consumer_config = {
            # Basic connection
            'bootstrap.servers': ','.join(self.cfg.kafka.brokers),
            'client.id': self.cfg.kafka.client_id,
            'group.id': self.cfg.consumer_groups.ai_server,

            # KafkaConsumer behavior
            'auto.offset.reset': self.cfg.kafka.auto_offset_reset,
            'enable.auto.commit': self.cfg.consumer.enable_auto_commit,
            'auto.commit.interval.ms': self.cfg.consumer.auto_commit_interval_ms,

            # Performance tuning
            'max.poll.interval.ms': self.cfg.consumer.max_poll_interval_ms,
            'session.timeout.ms': self.cfg.consumer.session_timeout_ms,
            'heartbeat.interval.ms': self.cfg.consumer.heartbeat_interval_ms,
            'fetch.min.bytes': self.cfg.consumer.fetch_min_bytes,
            'fetch.max.bytes': self.cfg.consumer.fetch_max_bytes,
            'fetch.max.wait.ms': self.cfg.consumer.fetch_max_wait_ms,
            'max.partition.fetch.bytes': self.cfg.consumer.max_partition_fetch_bytes,

            # Message processing
            'max.poll.records': self.cfg.consumer.max_poll_records,
        }

        # Add security config if present
        if hasattr(self.cfg, 'security') and hasattr(self.cfg.security, 'protocol'):
            consumer_config.update({
                'security.protocol': self.cfg.security.protocol,
                'sasl.mechanism': self.cfg.security.sasl.mechanism,
                'sasl.username': self.cfg.security.sasl.username,
                'sasl.password': self.cfg.security.sasl.password,
            })

        return consumer_config

    def _build_topic_list(self) -> List[str]:
        """Build a list of topics to subscribe to"""
        topics = [self.cfg.topics.recommendation_requests]

        # Add recommendation requests topic

        # Add user interaction topics
        prefix = self.cfg.topics.prefix
        suffix = self.cfg.topics.suffix

        for event_type in self.cfg.event_types.supported_events:
            topic_name = f"{prefix}{event_type}{suffix}"
            topics.append(topic_name)

        self.logger.info(f"Subscribing to topics: {topics}")
        return topics

    def connect(self) -> bool:
        """Initialize Kafka consumer connection"""
        try:
            config = self._build_consumer_config()
            self.consumer = KafkaConsumer(config)

            # Subscribe to topics
            topics = self._build_topic_list()
            self.consumer.subscribe(topics)

            self.logger.info("Kafka consumer connected successfully")
            self.running.set()
            return True

        except KafkaException as e:
            self.logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set message processing handler function"""
        self.message_handler = handler

    def _process_message(self, msg) -> Optional[Dict[str, Any]]:
        """Process an individual Kafka message"""
        try:
            # Parse message
            message_data = {
                'topic': msg.topic(),
                'partition': msg.partition(),
                'offset': msg.offset(),
                'key': msg.key().decode('utf-8') if msg.key() else None,
                'value': json.loads(msg.value().decode('utf-8')),
                'timestamp': msg.timestamp(),
                'headers': dict(msg.headers()) if msg.headers() else {}
            }

            return message_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON message: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return None

    def consume_messages(self, timeout: float = 1.0) -> None:
        """
        Main consume loop
        Args:
            timeout: Poll timeout in seconds
        """
        if not self.consumer:
            self.logger.error("KafkaConsumer not initialized. Call connect() first.")
            return

        if not self.message_handler:
            self.logger.error("Message handler not set. Call set_message_handler() first.")
            return

        self.logger.info("Starting message consumption...")

        try:
            while self.running.is_set():
                msg = self.consumer.poll(timeout=timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        self.logger.debug(f'Reached end of partition {msg.partition()}')
                        continue
                    else:
                        self.logger.error(f'Kafka error: {msg.error()}')
                        continue

                # Process message
                processed_msg = self._process_message(msg)
                if processed_msg:
                    try:
                        # Call message handler
                        self.message_handler(processed_msg)

                        # Manual commit if auto-commit is disabled
                        if not self.cfg.consumer.enable_auto_commit:
                            self.consumer.commit(msg)

                    except Exception as e:
                        self.logger.error(f"Error in message handler: {e}")
                        # Don't commit on handler error

        except KafkaException as e:
            self.logger.error(f"Kafka consumption error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during consumption: {e}")

    def consume_batch(self, max_messages: int = None, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """
        Consume messages in batch for ML processing
        Args:
            max_messages: Maximum messages per batch
            timeout: Poll timeout in seconds
        Returns:
            List of processed messages
        """
        if not self.consumer:
            self.logger.error("KafkaConsumer not initialized.")
            return []

        batch_size = max_messages or self.cfg.ai_server.model.batch_size
        messages = []

        try:
            for _ in range(batch_size):
                if not self.running.is_set():
                    break

                msg = self.consumer.poll(timeout=timeout)

                if msg is None:
                    break

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        self.logger.error(f'Kafka error: {msg.error()}')
                    continue

                processed_msg = self._process_message(msg)
                if processed_msg:
                    messages.append(processed_msg)

            # Commit batch if successful
            if messages and not self.cfg.consumer.enable_auto_commit:
                self.consumer.commit()

        except Exception as e:
            self.logger.error(f"Error in batch consumption: {e}")

        return messages

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()

    def shutdown(self):
        """Gracefully shutdown consumer"""
        self.logger.info("Shutting down Kafka consumer...")
        self.running.clear()

        if self.consumer:
            try:
                self.consumer.close()
                self.logger.info("Kafka consumer closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing consumer: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
