import json
import time
import csv
from datetime import datetime
from confluent_kafka import Producer
from pathlib import Path

KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'interactions'

CSV_FILE = '../test-data/interactions.csv'

def create_producer():
    """Create and configure Kafka producer."""
    config = {
        'bootstrap.servers': KAFKA_BROKER,
        'client.id': 'vrecom-test-producer'
    }
    return Producer(config)

def delivery_callback(err, msg):
    """Callback for message delivery reports."""
    if err:
        print(f'ERROR: Message delivery failed: {err}')
    else:
        print(f'SUCCESS: Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

def load_csv_data(csv_path):
    """Load interaction data from CSV file."""
    interactions = []
    csv_file_path = Path(__file__).parent / csv_path

    if not csv_file_path.exists():
        print(f"ERROR: CSV file not found at {csv_file_path}")
        return interactions

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            interactions.append({
                'user_id': row['user_id'],
                'item_id': row['item_id'],
                'rating': float(row['rating']),
                'timestamp': row['timestamp']
            })

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
            message = json.dumps(interaction).encode('utf-8')

            producer.produce(
                topic=TOPIC_NAME,
                value=message,
                key=interaction['user_id'].encode('utf-8'),
                callback=delivery_callback
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
            interaction_copy['timestamp'] = datetime.utcnow().isoformat() + 'Z'

            message = json.dumps(interaction_copy).encode('utf-8')

            producer.produce(
                topic=TOPIC_NAME,
                value=message,
                key=interaction_copy['user_id'].encode('utf-8'),
                callback=delivery_callback
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

    interactions = load_csv_data(CSV_FILE)

    if not interactions:
        print("ERROR: No data to send. Exiting.")
        return

    print(f"\nConnecting to Kafka broker: {KAFKA_BROKER}")
    producer = create_producer()

    print("\nSelect mode:")
    print("1. Send all data once (batch mode)")
    print("2. Send all data with delay (batch mode with delay)")
    print("3. Continuous stream (loop forever)")

    try:
        choice = input("\nEnter choice (1-3): ").strip()

        if choice == '1':
            send_to_kafka(producer, interactions, delay=0)
        elif choice == '2':
            delay = float(input("Enter delay between messages (seconds): "))
            send_to_kafka(producer, interactions, delay=delay)
        elif choice == '3':
            interval = float(input("Enter interval between messages (seconds): "))
            send_continuous_stream(producer, interactions, interval=interval)
        else:
            print("Invalid choice. Using batch mode with no delay.")
            send_to_kafka(producer, interactions, delay=0)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        print("\nClosing producer...")
        producer.flush()
        print("Done!")

if __name__ == '__main__':
    main()
