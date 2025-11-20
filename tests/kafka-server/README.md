# Kafka Test Server

A standalone Kafka server setup for testing purposes. This is completely isolated from the main project.

## Overview

This setup includes:
- Apache Kafka broker
- Zookeeper for Kafka coordination
- Kafka UI for easy management and monitoring

## Prerequisites

- Docker
- Docker Compose

## Getting Started

### Start the Kafka Server

```bash
docker-compose up -d
```

### Stop the Kafka Server

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

## Access Points

- **Kafka Broker**: `localhost:9092`
- **Kafka UI**: `http://localhost:8080`
- **Zookeeper**: `localhost:2181`

## Usage Examples

### Create a Topic

```bash
docker exec -it test_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --partitions 3 \
  --replication-factor 1
```

### List Topics

```bash
docker exec -it test_kafka kafka-topics --list \
  --bootstrap-server localhost:9092
```

### Produce Messages

```bash
docker exec -it test_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic test-topic
```

### Consume Messages

```bash
docker exec -it test_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --from-beginning
```

## Testing with Python

### Install Required Package

```bash
pip install confluent-kafka
```

### Producer Example

```python
from confluent_kafka import Producer
import json

config = {
    'bootstrap.servers': 'localhost:9092'
}

producer = Producer(config)

def delivery_callback(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Produce message
data = {'user_id': '123', 'item_id': '456', 'rating': 5.0}
producer.produce(
    'test-topic',
    json.dumps(data).encode('utf-8'),
    callback=delivery_callback
)
producer.flush()
```

### Consumer Example

```python
from confluent_kafka import Consumer
import json

config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(config)
consumer.subscribe(['test-topic'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f'Consumer error: {msg.error()}')
            continue

        data = json.loads(msg.value().decode('utf-8'))
        print(f'Received: {data}')
finally:
    consumer.close()
```

## Troubleshooting

### Connection Issues

If you cannot connect to Kafka from outside Docker:
- Ensure port 9092 is not being used by another service
- Check that Docker containers are running: `docker ps`
- Verify network connectivity: `docker network inspect kafka_test_network`

### Topic Not Found

If topics are not created automatically:
```bash
docker exec -it test_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic your-topic-name \
  --partitions 1 \
  --replication-factor 1
```

### Clean Reset

To completely reset Kafka state:
```bash
docker-compose down -v
docker-compose up -d
```

## Notes

- This setup uses a single broker with replication factor 1, suitable for testing only
- Data persists in Docker volumes. Use `docker-compose down -v` to remove all data
- Kafka UI provides a web interface for easier topic and message management
- This is completely isolated from the main VRecom project
