#!/usr/bin/env python3
"""
Kafka Connection Test Script
============================
Script tổng hợp để test kết nối Kafka cho cả Producer và Consumer.
Verify rằng hệ thống có thể gửi và nhận messages thành công.

Usage:
    python test_kafka_connection.py
"""

import json
import sys
import time
from datetime import datetime

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

# Configuration
KAFKA_BROKER = "localhost:9092"
TEST_TOPIC = "test_connection_topic"
TEST_GROUP_ID = "test_connection_consumer_group"
TEST_MESSAGES_COUNT = 100  # Increased for better model training


class KafkaConnectionTester:
    """Class để test kết nối Kafka"""

    def __init__(self):
        self.broker = KAFKA_BROKER
        self.topic = TEST_TOPIC
        self.group_id = TEST_GROUP_ID
        self.test_passed = 0
        self.test_failed = 0

        # Data generators for realistic test data
        self.users = [f"user_{i}" for i in range(1, 21)]  # 20 users
        self.items = [f"item_{i}" for i in range(1, 51)]  # 50 items

        # User preferences (some users prefer certain items)
        self.user_preferences = {
            "user_1": ["item_1", "item_2", "item_5", "item_10"],
            "user_2": ["item_3", "item_7", "item_15", "item_20"],
            "user_3": ["item_1", "item_8", "item_12", "item_25"],
            "user_4": ["item_5", "item_10", "item_15", "item_30"],
            "user_5": ["item_2", "item_9", "item_18", "item_35"],
        }

        # Item popularity (some items are more popular)
        self.popular_items = ["item_1", "item_5", "item_10", "item_15", "item_20"]

    def print_header(self, title):
        """In header cho mỗi test"""
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}")

    def print_success(self, message):
        """In success message"""
        print(f"✓ {message}")
        self.test_passed += 1

    def print_error(self, message):
        """In error message"""
        print(f"✗ {message}")
        self.test_failed += 1

    def print_info(self, message):
        """In info message"""
        print(f"  {message}")

    def test_broker_connection(self):
        """Test 1: Kiểm tra kết nối với Kafka broker"""
        self.print_header("TEST 1: Kafka Broker Connection")

        try:
            admin_client = AdminClient({"bootstrap.servers": self.broker})
            metadata = admin_client.list_topics(timeout=5)

            self.print_success(f"Connected to Kafka broker: {self.broker}")
            self.print_info(f"Cluster ID: {metadata.cluster_id}")
            self.print_info(f"Broker count: {len(metadata.brokers)}")
            self.print_info(f"Topic count: {len(metadata.topics)}")

            return True

        except Exception as e:
            self.print_error(f"Failed to connect to Kafka broker: {e}")
            return False

    def create_test_topic(self):
        """Test 2: Tạo test topic nếu chưa có"""
        self.print_header("TEST 2: Create Test Topic")

        try:
            admin_client = AdminClient({"bootstrap.servers": self.broker})

            # Check if topic exists
            metadata = admin_client.list_topics(timeout=5)
            if self.topic in metadata.topics:
                self.print_success(f"Topic '{self.topic}' already exists")
                return True

            # Create topic
            new_topic = NewTopic(self.topic, num_partitions=1, replication_factor=1)
            fs = admin_client.create_topics([new_topic])

            # Wait for topic creation
            for topic, f in fs.items():
                try:
                    f.result()
                    self.print_success(f"Topic '{topic}' created successfully")
                    return True
                except Exception as e:
                    self.print_error(f"Failed to create topic '{topic}': {e}")
                    return False

        except Exception as e:
            self.print_error(f"Topic creation error: {e}")
            return False

    def generate_realistic_interaction(self, message_id):
        """Generate realistic user-item interaction data"""
        import random

        # Select user (weighted towards active users)
        if random.random() < 0.3:  # 30% chance for active users
            user_id = random.choice(list(self.user_preferences.keys()))
        else:
            user_id = random.choice(self.users)

        # Select item based on user preference or popularity
        if user_id in self.user_preferences and random.random() < 0.5:
            # 50% chance to interact with preferred items
            item_id = random.choice(self.user_preferences[user_id])
            rating = random.choice([4.0, 4.5, 5.0])  # High ratings for preferred items
        elif random.random() < 0.3:
            # 30% chance to interact with popular items
            item_id = random.choice(self.popular_items)
            rating = random.choice([3.5, 4.0, 4.5, 5.0])
        else:
            # Random interaction
            item_id = random.choice(self.items)
            rating = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])

        return {
            "message_id": message_id,
            "user_id": user_id,
            "item_id": item_id,
            "rating": rating,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def test_producer(self):
        """Test 3: Test Producer - Gửi messages (không cần group.id)"""
        self.print_header("TEST 3: Kafka Producer (No group.id required)")

        try:
            # Producer configuration - NO group.id needed
            producer_config = {
                "bootstrap.servers": self.broker,
                "client.id": "test-producer",
            }

            producer = Producer(producer_config)
            self.print_success("Producer created successfully (without group.id)")

            sent_count = 0
            delivery_reports = []

            def delivery_callback(err, msg):
                if err:
                    delivery_reports.append(False)
                else:
                    delivery_reports.append(True)

            # Send test messages with realistic data
            self.print_info(
                f"Sending {TEST_MESSAGES_COUNT} realistic interaction messages..."
            )
            self.print_info(f"  - {len(self.users)} unique users")
            self.print_info(f"  - {len(self.items)} unique items")
            self.print_info(f"  - User preferences and item popularity patterns")

            for i in range(TEST_MESSAGES_COUNT):
                test_data = self.generate_realistic_interaction(i + 1)

                producer.produce(
                    topic=self.topic,
                    key=test_data["user_id"].encode("utf-8"),
                    value=json.dumps(test_data).encode("utf-8"),
                    callback=delivery_callback,
                )

                producer.poll(0)
                sent_count += 1

                # Progress indicator for large datasets
                if (i + 1) % 25 == 0:
                    self.print_info(
                        f"  Progress: {i + 1}/{TEST_MESSAGES_COUNT} messages sent"
                    )

            # Flush all messages
            producer.flush()
            time.sleep(1)  # Wait for delivery reports

            successful = sum(delivery_reports)
            self.print_success(
                f"Sent {sent_count} messages, {successful} delivered successfully"
            )

            # Print statistics
            self.print_info("Message statistics:")
            self.print_info(f"  - Diverse ratings: 1.0 to 5.0")
            self.print_info(f"  - User preference patterns included")
            self.print_info(f"  - Popular items weighted appropriately")

            return successful == TEST_MESSAGES_COUNT

        except Exception as e:
            self.print_error(f"Producer test failed: {e}")
            return False

    def test_consumer(self):
        """Test 4: Test Consumer - Nhận messages (CẦN group.id)"""
        self.print_header("TEST 4: Kafka Consumer (group.id REQUIRED)")

        try:
            # Consumer configuration - group.id is REQUIRED
            consumer_config = {
                "bootstrap.servers": self.broker,
                "group.id": self.group_id,  # BẮT BUỘC
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
                "client.id": "test-consumer",
            }

            consumer = Consumer(consumer_config)
            self.print_success(
                f"Consumer created successfully (with group.id: {self.group_id})"
            )

            consumer.subscribe([self.topic])
            self.print_info(f"Subscribed to topic: {self.topic}")

            # Consume messages
            received_count = 0
            timeout = 10  # seconds
            start_time = time.time()

            self.print_info(f"Consuming messages (timeout: {timeout}s)...")

            while received_count < TEST_MESSAGES_COUNT:
                if time.time() - start_time > timeout:
                    self.print_error(
                        f"Timeout: Only received {received_count}/{TEST_MESSAGES_COUNT} messages"
                    )
                    consumer.close()
                    return False

                msg = consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        self.print_error(f"Consumer error: {msg.error()}")
                        continue

                received_count += 1
                data = json.loads(msg.value().decode("utf-8"))
                self.print_info(
                    f"  Received message {received_count}: "
                    f"user_id={data['user_id']}, item_id={data['item_id']}"
                )

            consumer.close()
            self.print_success(
                f"Successfully received all {TEST_MESSAGES_COUNT} messages"
            )

            return True

        except Exception as e:
            self.print_error(f"Consumer test failed: {e}")
            return False

    def test_consumer_without_group_id(self):
        """Test 5: Verify Consumer FAILS without group.id"""
        self.print_header("TEST 5: Verify Consumer Requires group.id")

        try:
            # Try to create consumer WITHOUT group.id
            consumer_config = {
                "bootstrap.servers": self.broker,
                # Missing group.id
                "auto.offset.reset": "earliest",
            }

            try:
                consumer = Consumer(consumer_config)
                consumer.subscribe([self.topic])
                msg = consumer.poll(timeout=1.0)
                consumer.close()

                # If we get here, it means consumer worked without group.id (unexpected)
                self.print_error(
                    "UNEXPECTED: Consumer worked without group.id (this should fail)"
                )
                return False

            except Exception as e:
                # This is expected - consumer should fail without group.id
                self.print_success(
                    f"✓ Confirmed: Consumer requires group.id (Error: {type(e).__name__})"
                )
                return True

        except Exception as e:
            self.print_error(f"Test verification failed: {e}")
            return False

    def run_all_tests(self):
        """Chạy tất cả tests"""
        self.print_header("VRecommendation Kafka Connection Test Suite")
        print(f"Broker: {self.broker}")
        print(f"Test Topic: {self.topic}")
        print(f"Consumer Group ID: {self.group_id}")

        # Run tests
        test1 = self.test_broker_connection()
        if not test1:
            self.print_error("Broker connection failed. Stopping tests.")
            return False

        test2 = self.create_test_topic()
        test3 = self.test_producer()
        test4 = self.test_consumer()
        test5 = self.test_consumer_without_group_id()

        # Summary
        self.print_header("TEST SUMMARY")
        print(f"Tests Passed: {self.test_passed}")
        print(f"Tests Failed: {self.test_failed}")

        if self.test_failed == 0:
            print("\n✓ ALL TESTS PASSED!")
            print("\nKết luận:")
            print("  • Producer hoạt động tốt (không cần group.id)")
            print("  • Consumer hoạt động tốt (cần group.id)")
            print("  • Kafka broker kết nối thành công")
            print("  • Hệ thống sẵn sàng để sử dụng!")
            return True
        else:
            print(f"\n✗ {self.test_failed} TEST(S) FAILED")
            print("\nVui lòng kiểm tra:")
            print("  1. Kafka broker đã chạy chưa? (docker-compose up -d)")
            print("  2. Port 9092 có bị chặn không?")
            print("  3. confluent-kafka đã cài đặt chưa? (pip install confluent-kafka)")
            return False


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("  VRecommendation - Kafka Connection Test")
    print("=" * 70)
    print(f"\nTest Configuration:")
    print(f"  Messages: {TEST_MESSAGES_COUNT}")
    print(f"  Purpose: Generate realistic training data for recommendation model")

    # Check if Kafka is running
    print("\nĐảm bảo Kafka server đang chạy:")
    print("  cd tests/kafka-server")
    print("  docker-compose up -d")
    print("\nBắt đầu test trong 3 giây...")
    time.sleep(3)

    try:
        tester = KafkaConnectionTester()
        success = tester.run_all_tests()

        if success:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
