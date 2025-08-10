"""
Messaging interface module for different messaging systems.
Provides abstract base classes for producers, consumers, and managers.
Compatible with Python 3.9.23 and PyRight type checking.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union, AsyncGenerator, Generator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Message status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class CompressionType(Enum):
    """Compression type enumeration."""
    NONE = "none"
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"


@dataclass
class Message:
    """Generic message structure."""
    key: Optional[str] = None
    value: Any = None
    headers: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    partition: Optional[int] = None
    offset: Optional[int] = None
    topic: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.headers is None:
            self.headers = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProducerConfig:
    """Producer configuration."""
    bootstrap_servers: List[str]
    client_id: Optional[str] = None
    compression_type: CompressionType = CompressionType.NONE
    batch_size: int = 16384
    linger_ms: int = 0
    buffer_memory: int = 33554432
    max_request_size: int = 1048576
    retries: int = 3
    acks: str = "1"
    enable_idempotence: bool = False
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class ConsumerConfig:
    """Consumer configuration."""
    bootstrap_servers: List[str]
    group_id: str
    client_id: Optional[str] = None
    auto_offset_reset: str = "latest"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 30000
    heartbeat_interval_ms: int = 3000
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


@dataclass
class TopicConfig:
    """Topic configuration."""
    name: str
    num_partitions: int = 1
    replication_factor: int = 1
    config: Optional[Dict[str, str]] = None


class MessageHandler(ABC):
    """Abstract message handler interface."""

    @abstractmethod
    def handle_message(self, message: Message) -> bool:
        """
        Handle incoming message.

        Args:
            message: The message to handle

        Returns:
            bool: True if message was handled successfully, False otherwise
        """
        pass

    @abstractmethod
    def handle_error(self, error: Exception, message: Optional[Message] = None) -> None:
        """
        Handle processing errors.

        Args:
            error: The error that occurred
            message: The message being processed when error occurred (if any)
        """
        pass


class MessagingProducer(ABC):
    """Abstract producer interface."""

    def __init__(self, config: ProducerConfig) -> None:
        self.config = config
        self._connected = False

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to messaging system."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to messaging system."""
        pass

    @abstractmethod
    def send_message(
            self,
            topic: str,
            message: Message,
            callback: Optional[Callable[[Message, Optional[Exception]], None]] = None
    ) -> bool:
        """
        Send a single message.

        Args:
            topic: Topic to send message to
            message: Message to send
            callback: Optional callback for delivery confirmation

        Returns:
            bool: True if message was queued successfully
        """
        pass

    @abstractmethod
    def send_messages(
            self,
            topic: str,
            messages: List[Message],
            callback: Optional[Callable[[List[Message], Optional[Exception]], None]] = None
    ) -> int:
        """
        Send multiple messages.

        Args:
            topic: Topic to send messages to
            messages: List of messages to send
            callback: Optional callback for delivery confirmation

        Returns:
            int: Number of messages queued successfully
        """
        pass

    @abstractmethod
    def flush(self, timeout: Optional[float] = None) -> bool:
        """
        Flush pending messages.

        Args:
            timeout: Timeout in seconds

        Returns:
            bool: True if all messages were flushed successfully
        """
        pass

    @property
    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._connected


class MessagingConsumer(ABC):
    """Abstract consumer interface."""

    def __init__(self, config: ConsumerConfig) -> None:
        self.config = config
        self._connected = False
        self._subscribed_topics: List[str] = []

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to messaging system."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to messaging system."""
        pass

    @abstractmethod
    def subscribe(self, topics: Union[str, List[str]]) -> None:
        """
        Subscribe to topics.

        Args:
            topics: Topic name or list of topic names
        """
        pass

    @abstractmethod
    def unsubscribe(self) -> None:
        """Unsubscribe from all topics."""
        pass

    @abstractmethod
    def poll(self, timeout_ms: int = 1000) -> List[Message]:
        """
        Poll for messages.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    def commit(self, offsets: Optional[Dict[str, int]] = None) -> None:
        """
        Commit message offsets.

        Args:
            offsets: Optional specific offsets to commit
        """
        pass

    @abstractmethod
    def seek(self, topic: str, partition: int, offset: int) -> None:
        """
        Seek to specific offset.

        Args:
            topic: Topic name
            partition: Partition number
            offset: Offset to seek to
        """
        pass

    @abstractmethod
    def consume_messages(
            self,
            handler: MessageHandler,
            timeout_ms: int = 1000,
            max_messages: Optional[int] = None
    ) -> None:
        """
        Consume messages with handler.

        Args:
            handler: Message handler
            timeout_ms: Poll timeout in milliseconds
            max_messages: Maximum number of messages to process
        """
        pass

    @property
    def is_connected(self) -> bool:
        """Check if consumer is connected."""
        return self._connected

    @property
    def subscribed_topics(self) -> List[str]:
        """Get list of subscribed topics."""
        return self._subscribed_topics.copy()


class TopicManager(ABC):
    """Abstract topic manager interface."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to messaging system."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to messaging system."""
        pass

    @abstractmethod
    def create_topic(self, topic_config: TopicConfig) -> bool:
        """
        Create a topic.

        Args:
            topic_config: Topic configuration

        Returns:
            bool: True if topic was created successfully
        """
        pass

    @abstractmethod
    def delete_topic(self, topic_name: str) -> bool:
        """
        Delete a topic.

        Args:
            topic_name: Name of topic to delete

        Returns:
            bool: True if topic was deleted successfully
        """
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        """
        List all topics.

        Returns:
            List of topic names
        """
        pass

    @abstractmethod
    def topic_exists(self, topic_name: str) -> bool:
        """
        Check if topic exists.

        Args:
            topic_name: Topic name to check

        Returns:
            bool: True if topic exists
        """
        pass

    @abstractmethod
    def get_topic_metadata(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """
        Get topic metadata.

        Args:
            topic_name: Topic name

        Returns:
            Dictionary with topic metadata or None if not found
        """
        pass

    @abstractmethod
    def update_topic_config(self, topic_name: str, config: Dict[str, str]) -> bool:
        """
        Update topic configuration.

        Args:
            topic_name: Topic name
            config: Configuration updates

        Returns:
            bool: True if configuration was updated successfully
        """
        pass


class MessagingManager(ABC):
    """Abstract messaging manager interface."""

    @abstractmethod
    def get_producer(self, config: ProducerConfig) -> MessagingProducer:
        """
        Get a producer instance.

        Args:
            config: Producer configuration

        Returns:
            Producer instance
        """
        pass

    @abstractmethod
    def get_consumer(self, config: ConsumerConfig) -> MessagingConsumer:
        """
        Get a consumer instance.

        Args:
            config: Consumer configuration

        Returns:
            Consumer instance
        """
        pass

    @abstractmethod
    def get_topic_manager(self, bootstrap_servers: List[str]) -> TopicManager:
        """
        Get a topic manager instance.

        Args:
            bootstrap_servers: List of bootstrap servers

        Returns:
            Topic manager instance
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on messaging system.

        Returns:
            Dictionary with health check results
        """
        pass


# Utility functions
def serialize_message(message: Message, serializer: Optional[Callable[[Any], bytes]] = None) -> bytes:
    """
    Serialize message value.

    Args:
        message: Message to serialize
        serializer: Custom serializer function

    Returns:
        Serialized message as bytes
    """
    if serializer:
        return serializer(message.value)

    if isinstance(message.value, bytes):
        return message.value
    elif isinstance(message.value, str):
        return message.value.encode('utf-8')
    elif message.value is None:
        return b''
    else:
        # Default JSON serialization
        import json
        return json.dumps(message.value).encode('utf-8')


def deserialize_message(
        data: bytes,
        deserializer: Optional[Callable[[bytes], Any]] = None
) -> Any:
    """
    Deserialize message data.

    Args:
        data: Raw message data
        deserializer: Custom deserializer function

    Returns:
        Deserialized message value
    """
    if deserializer:
        return deserializer(data)

    try:
        # Try JSON deserialization first
        import json
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Fallback to string
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            # Return raw bytes if can't decode
            return data


# Exception classes
class MessagingError(Exception):
    """Base messaging exception."""
    pass


class ConnectionError(MessagingError):
    """Connection related errors."""
    pass


class ProducerError(MessagingError):
    """Producer related errors."""
    pass


class ConsumerError(MessagingError):
    """Consumer related errors."""
    pass


class TopicError(MessagingError):
    """Topic management related errors."""
    pass


class SerializationError(MessagingError):
    """Serialization related errors."""
    pass
