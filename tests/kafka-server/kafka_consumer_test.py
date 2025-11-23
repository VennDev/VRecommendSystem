import json
import time
from datetime import datetime

from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "interactions"
GROUP_ID = "vrecom-test-consumer-group"


def create_consumer():
    """Create and configure Kafka consumer with group.id."""
    config = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 1000,
        "session.timeout.ms": 6000,
        "client.id": "vrecom-test-consumer",
    }
    return Consumer(config)


def consume_messages(consumer, max_messages=None, timeout=10):
    """
    Consume messages from Kafka topic.

    :param consumer: Kafka consumer instance
    :param max_messages: Maximum number of messages to consume (None = unlimited)
    :param timeout: Timeout in seconds for polling messages
    """
    print("\n" + "=" * 60)
    print("VRecommendation Kafka Consumer Test")
    print("=" * 60)
    print(f"Broker: {KAFKA_BROKER}")
    print(f"Topic: {TOPIC_NAME}")
    print(f"Group ID: {GROUP_ID}")
    print(f"Max Messages: {max_messages if max_messages else 'Unlimited'}")
    print(f"{'=' * 60}\n")

    # Subscribe to topic
    consumer.subscribe([TOPIC_NAME])
    print(f"Subscribed to topic '{TOPIC_NAME}'")
    print("Waiting for messages... (Press Ctrl+C to stop)\n")
    print("-" * 60)

    message_count = 0
    success_count = 0
    error_count = 0

    try:
        while True:
            # Check if we've reached max messages
            if max_messages and message_count >= max_messages:
                print(f"\nReached maximum message count ({max_messages})")
                break

            # Poll for messages
            msg = consumer.poll(timeout=timeout)

            if msg is None:
                print(f"\nNo message received within {timeout} seconds")
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    print(f"Reached end of partition {msg.partition()}")
                    continue
                else:
                    error_count += 1
                    print(f"ERROR: {msg.error()}")
                    continue

            # Successfully received a message
            message_count += 1
            success_count += 1

            try:
                # Decode and parse message
                key = msg.key().decode("utf-8") if msg.key() else None
                value = msg.value().decode("utf-8")
                data = json.loads(value)

                # Display message info
                print(f"\n[Message #{message_count}]")
                print(f"  Partition: {msg.partition()}")
                print(f"  Offset: {msg.offset()}")
                print(f"  Key: {key}")
                print(
                    f"  Timestamp: {datetime.fromtimestamp(msg.timestamp()[1] / 1000).isoformat()}"
                )
                print(f"  Data:")
                for field, val in data.items():
                    print(f"    - {field}: {val}")
                print("-" * 60)

            except json.JSONDecodeError as e:
                error_count += 1
                print(f"ERROR: Failed to parse JSON - {e}")
                print(f"  Raw value: {value}")
            except Exception as e:
                error_count += 1
                print(f"ERROR: Failed to process message - {e}")

            # Small delay to make output readable
            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n\nStopped by user (Ctrl+C)")

    finally:
        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"  Total messages received: {message_count}")
        print(f"  Successfully processed: {success_count}")
        print(f"  Errors: {error_count}")
        print("=" * 60)

        # Close consumer
        print("\nClosing consumer...")
        consumer.close()
        print("Consumer closed successfully!")


def test_connection():
    """Test basic connection to Kafka broker."""
    print("\n" + "=" * 60)
    print("Testing Kafka Connection")
    print("=" * 60)

    try:
        consumer = create_consumer()
        print("✓ Successfully created consumer")
        print(f"✓ Broker: {KAFKA_BROKER}")
        print(f"✓ Group ID: {GROUP_ID}")

        # Try to get metadata
        print("\nFetching cluster metadata...")
        metadata = consumer.list_topics(timeout=5)

        print("✓ Connected to cluster")
        print(f"  Broker count: {len(metadata.brokers)}")
        print(f"  Topic count: {len(metadata.topics)}")

        if TOPIC_NAME in metadata.topics:
            topic_metadata = metadata.topics[TOPIC_NAME]
            print(f"\n✓ Topic '{TOPIC_NAME}' found:")
            print(f"    Partitions: {len(topic_metadata.partitions)}")
            for partition_id, partition in topic_metadata.partitions.items():
                print(f"      - Partition {partition_id}: Leader={partition.leader}")
        else:
            print(f"\n✗ Topic '{TOPIC_NAME}' not found!")
            print("  Available topics:")
            for topic in metadata.topics:
                print(f"    - {topic}")

        consumer.close()
        print("\n✓ Connection test successful!")
        return True

    except KafkaException as e:
        print(f"\n✗ Connection test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("VRecommendation Kafka Consumer Test Tool")
    print("=" * 60)

    print("\nSelect mode:")
    print("1. Test connection only")
    print("2. Consume messages (limited)")
    print("3. Consume messages (continuous)")
    print("4. Consume messages (from beginning)")

    try:
        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            test_connection()

        elif choice == "2":
            max_msg = int(input("Enter maximum number of messages to consume: "))
            timeout = float(input("Enter timeout in seconds (default 10): ") or "10")
            consumer = create_consumer()
            consume_messages(consumer, max_messages=max_msg, timeout=timeout)

        elif choice == "3":
            timeout = float(input("Enter timeout in seconds (default 10): ") or "10")
            consumer = create_consumer()
            consume_messages(consumer, max_messages=None, timeout=timeout)

        elif choice == "4":
            print("\nConsuming from beginning (earliest offset)...")
            max_msg = int(
                input("Enter maximum number of messages (0 for unlimited): ") or "0"
            )
            timeout = float(input("Enter timeout in seconds (default 10): ") or "10")
            consumer = create_consumer()
            if max_msg > 0:
                consume_messages(consumer, max_messages=max_msg, timeout=timeout)
            else:
                consume_messages(consumer, max_messages=None, timeout=timeout)
        else:
            print("Invalid choice. Testing connection...")
            test_connection()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except ValueError as e:
        print(f"\nInvalid input: {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\nDone!")


if __name__ == "__main__":
    main()
