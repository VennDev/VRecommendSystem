import csv
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

from confluent_kafka import Producer

KAFKA_BROKER = "localhost:9092"
TOPIC_NAME = "interactions"

CSV_FILE = "../test-data/interactions.csv"

# Realistic data generators
USERS = [f"user_{i}" for i in range(1, 101)]  # 100 users
ITEMS = [f"item_{i}" for i in range(1, 201)]  # 200 items

# User preference patterns (some users like certain categories)
USER_PREFERENCES = {
    "user_1": ["item_1", "item_5", "item_10", "item_15", "item_20"],
    "user_2": ["item_3", "item_7", "item_12", "item_17", "item_25"],
    "user_3": ["item_2", "item_8", "item_14", "item_22", "item_30"],
    "user_4": ["item_4", "item_9", "item_18", "item_28", "item_35"],
    "user_5": ["item_6", "item_11", "item_19", "item_29", "item_40"],
    "user_10": ["item_1", "item_10", "item_20", "item_30", "item_40"],
    "user_15": ["item_5", "item_15", "item_25", "item_35", "item_45"],
    "user_20": ["item_2", "item_12", "item_22", "item_32", "item_42"],
}

# Popular items (higher interaction rate)
POPULAR_ITEMS = [
    "item_1",
    "item_5",
    "item_10",
    "item_15",
    "item_20",
    "item_25",
    "item_30",
    "item_35",
    "item_40",
    "item_50",
]

# Item categories for pattern learning
ITEM_CATEGORIES = {
    "electronics": [f"item_{i}" for i in range(1, 41)],
    "fashion": [f"item_{i}" for i in range(41, 81)],
    "home": [f"item_{i}" for i in range(81, 121)],
    "sports": [f"item_{i}" for i in range(121, 161)],
    "books": [f"item_{i}" for i in range(161, 201)],
}


def create_producer():
    """Create and configure Kafka producer."""
    config = {"bootstrap.servers": KAFKA_BROKER, "client.id": "vrecom-test-producer"}
    return Producer(config)


def delivery_callback(err, msg):
    """Callback for message delivery reports."""
    if err:
        print(f"ERROR: Message delivery failed: {err}")
    else:
        print(
            f"SUCCESS: Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
        )


def generate_realistic_interaction(base_timestamp):
    """Generate a single realistic user-item interaction."""
    # Select user (weighted towards active users)
    if random.random() < 0.3:  # 30% active users
        user_id = random.choice(list(USER_PREFERENCES.keys()))
    else:
        user_id = random.choice(USERS)

    # Select item based on user preference or popularity
    if user_id in USER_PREFERENCES and random.random() < 0.6:
        # 60% chance to interact with preferred items
        item_id = random.choice(USER_PREFERENCES[user_id])
        rating = random.choice([4.0, 4.5, 5.0])  # High ratings for preferences
    elif random.random() < 0.3:
        # 30% chance for popular items
        item_id = random.choice(POPULAR_ITEMS)
        rating = random.choice([3.5, 4.0, 4.5, 5.0])
    else:
        # Random interaction with diverse ratings
        item_id = random.choice(ITEMS)
        rating = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])

    # Add some time variance
    time_offset = timedelta(seconds=random.randint(0, 3600))
    timestamp = (base_timestamp + time_offset).isoformat() + "Z"

    return {
        "user_id": user_id,
        "item_id": item_id,
        "rating": rating,
        "timestamp": timestamp,
    }


def generate_synthetic_data(count=1000):
    """Generate synthetic interaction data with realistic patterns."""
    interactions = []
    base_timestamp = datetime.utcnow() - timedelta(days=30)  # Start 30 days ago

    print(f"Generating {count} synthetic interactions...")
    print(f"  - {len(USERS)} unique users")
    print(f"  - {len(ITEMS)} unique items")
    print(f"  - User preference patterns included")
    print(f"  - Popular items weighted appropriately")

    for i in range(count):
        interaction = generate_realistic_interaction(base_timestamp)
        interactions.append(interaction)

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{count} interactions...")

    print(f"✓ Generated {len(interactions)} synthetic interactions")
    return interactions


def load_csv_data(csv_path):
    """Load interaction data from CSV file."""
    interactions = []
    csv_file_path = Path(__file__).parent / csv_path

    if not csv_file_path.exists():
        print(f"WARNING: CSV file not found at {csv_file_path}")
        print(f"Will use synthetic data generation instead")
        return interactions

    with open(csv_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            interactions.append(
                {
                    "user_id": row["user_id"],
                    "item_id": row["item_id"],
                    "rating": float(row["rating"]),
                    "timestamp": row["timestamp"],
                }
            )

    print(f"Loaded {len(interactions)} interactions from CSV")
    return interactions


def send_to_kafka(producer, interactions, delay=0.1):
    """Send interaction data to Kafka topic."""
    print(f"\nSending {len(interactions)} messages to Kafka topic '{TOPIC_NAME}'...")
    print(f"Broker: {KAFKA_BROKER}")
    print("-" * 60)

    success_count = 0
    error_count = 0

    for idx, interaction in enumerate(interactions, 1):
        try:
            message = json.dumps(interaction).encode("utf-8")

            producer.produce(
                topic=TOPIC_NAME,
                value=message,
                key=interaction["user_id"].encode("utf-8"),
                callback=delivery_callback,
            )

            producer.poll(0)
            success_count += 1

            if delay > 0:
                time.sleep(delay)

            if idx % 10 == 0:
                print(f"Progress: {idx}/{len(interactions)} messages sent")
                producer.flush()

        except Exception as e:
            print(f"ERROR sending message {idx}: {e}")
            error_count += 1

    print("\nFlushing remaining messages...")
    producer.flush()

    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Total messages: {len(interactions)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print("=" * 60)


def send_continuous_stream(producer, interactions, interval=1):
    """Send messages continuously in a loop."""
    print(f"\nStarting continuous stream mode (Ctrl+C to stop)...")
    print(f"Sending messages every {interval} seconds")
    print("-" * 60)

    try:
        count = 0
        while True:
            interaction = interactions[count % len(interactions)]

            interaction_copy = interaction.copy()
            interaction_copy["timestamp"] = datetime.utcnow().isoformat() + "Z"

            message = json.dumps(interaction_copy).encode("utf-8")

            producer.produce(
                topic=TOPIC_NAME,
                value=message,
                key=interaction_copy["user_id"].encode("utf-8"),
                callback=delivery_callback,
            )

            producer.poll(0)
            count += 1

            if count % 10 == 0:
                producer.flush()
                print(f"Sent {count} messages...")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\nStopped after sending {count} messages")
        producer.flush()


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("VRecommendation Kafka Producer")
    print("=" * 60)

    print("\nData source selection:")
    print("1. Load from CSV file (if available)")
    print("2. Generate synthetic data (realistic patterns)")
    print("3. Generate large dataset (for model training)")

    try:
        data_choice = input("\nEnter choice (1-3): ").strip()

        if data_choice == "1":
            interactions = load_csv_data(CSV_FILE)
            if not interactions:
                print("\nFalling back to synthetic data generation...")
                interactions = generate_synthetic_data(500)
        elif data_choice == "2":
            count = int(
                input("How many interactions to generate? (default: 1000): ") or "1000"
            )
            interactions = generate_synthetic_data(count)
        elif data_choice == "3":
            count = int(
                input("How many interactions to generate? (recommended: 5000-10000): ")
                or "5000"
            )
            print(f"\n⚠ Generating large dataset for model training...")
            interactions = generate_synthetic_data(count)
        else:
            print("Invalid choice. Using default synthetic data.")
            interactions = generate_synthetic_data(1000)

        if not interactions:
            print("ERROR: No data to send. Exiting.")
            return

        print(f"\n✓ Ready to send {len(interactions)} interactions")
        print(f"Connecting to Kafka broker: {KAFKA_BROKER}")
        producer = create_producer()

        print("\nSending mode:")
        print("1. Send all data once (batch mode - fastest)")
        print("2. Send all data with delay (batch mode with delay)")
        print("3. Continuous stream (loop forever)")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            send_to_kafka(producer, interactions, delay=0)
        elif choice == "2":
            delay = float(input("Enter delay between messages (seconds): "))
            send_to_kafka(producer, interactions, delay=delay)
        elif choice == "3":
            interval = float(input("Enter interval between messages (seconds): "))
            send_continuous_stream(producer, interactions, interval=interval)
        else:
            print("Invalid choice. Using batch mode with no delay.")
            send_to_kafka(producer, interactions, delay=0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except ValueError as e:
        print(f"\nERROR: Invalid input - {e}")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\nClosing producer...")
        producer.flush()
        print("Done!")


if __name__ == "__main__":
    main()
