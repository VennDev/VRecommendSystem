# Kafka Test Server

A standalone Kafka server setup for testing purposes. This is completely isolated from the main project.

## Overview

This setup includes:
- Apache Kafka broker
- Zookeeper for Kafka coordination
- Kafka UI for easy management and monitoring
- **Producer Script** (`kafka_producer.py`) - Gửi messages vào Kafka topic với synthetic data generation
- **Consumer Test Script** (`kafka_consumer_test.py`) - Nhận messages từ Kafka topic với group.id
- **Training Data Generator** (`generate_training_data.py`) - Tạo large realistic datasets cho model training

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

## Python Testing Scripts

### 1. Kafka Producer (`kafka_producer.py`)

Script này hoạt động như một **Producer** - gửi messages vào Kafka topic.

**Lưu ý quan trọng:** Producer không cần `group.id` vì nó chỉ gửi dữ liệu, không nhận dữ liệu.

#### Sử dụng Producer:

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy producer
python kafka_producer.py
```

Chọn mode:
1. **Batch mode** - Gửi tất cả dữ liệu một lần
2. **Batch with delay** - Gửi với độ trễ giữa các messages
3. **Continuous stream** - Gửi liên tục (loop forever)

### 2. Kafka Consumer Test (`kafka_consumer_test.py`)

Script này hoạt động như một **Consumer** - nhận messages từ Kafka topic.

**Lưu ý quan trọng:** Consumer **BẮT BUỘC** phải có `group.id` để Kafka có thể:
- Theo dõi offset (vị trí đã đọc) của consumer
- Phân phối messages giữa các consumers trong cùng group
- Đảm bảo mỗi message chỉ được xử lý một lần trong mỗi group

#### Configuration Consumer:

```python
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'vrecom-test-consumer-group',  # BẮT BUỘC cho Consumer
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
}
```

#### Sử dụng Consumer Test:

```bash
# Cài đặt dependencies (nếu chưa)
pip install -r requirements.txt

# Chạy consumer test
python kafka_consumer_test.py
```

Chọn mode test:
1. **Test connection only** - Kiểm tra kết nối với Kafka broker
2. **Consume messages (limited)** - Nhận số lượng messages giới hạn
3. **Consume messages (continuous)** - Nhận liên tục cho đến khi Ctrl+C
4. **Consume messages (from beginning)** - Đọc từ đầu topic

### Sự khác biệt giữa Producer và Consumer:

| Đặc điểm | Producer | Consumer |
|----------|----------|----------|
| Chức năng | Gửi messages | Nhận messages |
| `group.id` | **Không cần** | **BẮT BUỘC** |
| Config quan trọng | `bootstrap.servers`, `client.id` | `bootstrap.servers`, `group.id`, `auto.offset.reset` |
| Sử dụng trong hệ thống | Backend application gửi events | VRecommendation AI Server nhận dữ liệu training |

### Workflow Test Hoàn Chỉnh:

```bash
# Bước 1: Start Kafka server
docker-compose up -d

# Bước 2: Mở terminal 1 - Chạy Consumer (nhận messages)
python kafka_consumer_test.py
# Chọn mode 3 (continuous)

# Bước 3: Mở terminal 2 - Chạy Producer (gửi messages)
python kafka_producer.py
# Chọn mode 1 hoặc 2

# Bước 4: Xem messages được nhận ở terminal 1
# Consumer sẽ hiển thị tất cả messages được gửi từ Producer
```

## Generating Large Training Datasets

Để train model hiệu quả, bạn cần nhiều dữ liệu realistic. Chúng tôi cung cấp 3 cách:

### Option 1: Training Data Generator (Recommended cho Production Training)

Script chuyên dụng để tạo large datasets với patterns realistic:

```bash
python generate_training_data.py
```

**Features:**
- Configurable users, items, và interactions
- Realistic user behavior patterns (20% users tạo 80% interactions)
- Item categories và popularity distributions
- User preference clustering (tech enthusiasts, fashion lovers, etc.)
- Temporal dynamics (spread over 30 days)
- Diverse rating distributions
- Export to CSV, JSON, hoặc gửi trực tiếp vào Kafka

**Example: Generate 10,000 interactions**
```bash
python generate_training_data.py
# Configuration:
#   Number of users: 200
#   Number of items: 500
#   Number of interactions: 10000
# Output format:
#   Option 3: Send to Kafka (hoặc 4 cho all formats)
```

**Kết quả:**
```
Dataset Statistics
======================================================================
Total Users: 200
Total Items: 500
Total Interactions: 10000
Unique Active Users: 160
Unique Items with Interactions: 450

Average Rating: 3.85
Avg Interactions per User: 62.5
Max Interactions per User: 150
Min Interactions per User: 5

Rating Distribution:
  1.0:   500 ( 5.00%)
  1.5:   450 ( 4.50%)
  2.0:   550 ( 5.50%)
  2.5:   600 ( 6.00%)
  3.0:  1200 (12.00%)
  3.5:  1300 (13.00%)
  4.0:  2100 (21.00%)
  4.5:  1800 (18.00%)
  5.0:  1500 (15.00%)
```

### Option 2: Enhanced Producer với Synthetic Data

Producer script hiện có synthetic data generation built-in:

```bash
python kafka_producer.py
# Data source: Option 2 (Generate synthetic data)
# Count: 5000 interactions (hoặc tùy chọn)
```

**Features:**
- 100 users, 200 items
- User preference patterns
- Popular items weighting
- Realistic rating distributions

### Option 3: Automated Test với Realistic Data

Test suite cũng tạo realistic data:

```bash
python test_kafka_connection.py
# Automatically generates 100 interactions với patterns
```

### Recommended Workflow cho Model Training

```bash
# Bước 1: Start Kafka
docker-compose up -d

# Bước 2: Generate large training dataset
python generate_training_data.py
# Chọn:
#   - Users: 500
#   - Items: 1000
#   - Interactions: 50000
#   - Output: Send to Kafka

# Bước 3: Verify data received
python kafka_consumer_test.py
# Chọn mode 2 (limited) để xem sample data

# Bước 4: Train model với VRecommendation
# Model sẽ có đủ data phong phú để học patterns
```

### Data Patterns Included

**User Behavior Patterns:**
- Active users (20%) tạo 80% interactions (Pareto principle)
- User preference clustering (tech, fashion, home, sports, books)
- Temporal dynamics (interactions spread over time)

**Item Patterns:**
- Popular items (top 10%) có nhiều interactions hơn
- Category-based clustering
- Diverse rating distributions based on match

**Rating Patterns:**
- Preferred items: 4.0-5.0 (high ratings)
- Popular items: 3.0-5.0 (good ratings)
- Random items: 1.0-5.0 (diverse ratings)
- Natural distribution mimicking real user behavior

## Training Data Comparison

| Method | Users | Items | Interactions | Best For |
|--------|-------|-------|--------------|----------|
| `test_kafka_connection.py` | 20 | 50 | 100 | Quick testing |
| `kafka_producer.py` (synthetic) | 100 | 200 | 1000-10000 | Medium testing |
| `generate_training_data.py` | Configurable | Configurable | 10000-100000+ | **Production training** |

**Recommendation:** 
- Development/Testing: Use `test_kafka_connection.py` hoặc `kafka_producer.py`
- Production Training: Use `generate_training_data.py` với 20000+ interactions

## Quick Start with Test Runner Scripts

Để dễ dàng hơn trong việc test, chúng tôi đã cung cấp scripts tự động:

### Windows Users

```cmd
# Chạy test runner menu
run_tests.cmd
```

Script sẽ hiển thị menu với các tùy chọn:
- Start/Stop Kafka Server
- Run Connection Test (kiểm tra toàn bộ hệ thống)
- Run Producer Test
- Run Consumer Test
- Show Status & Logs

### Linux/Mac Users

```bash
# Làm cho script có thể thực thi
chmod +x run_tests.sh

# Chạy test runner menu
./run_tests.sh
```

### Automated Full Connection Test

Để test toàn bộ hệ thống một lần (kiểm tra Producer, Consumer, và group.id):

```bash
# Windows
python test_kafka_connection.py

# Linux/Mac
python test_kafka_connection.py
```

Script này sẽ tự động:
1. ✓ Kiểm tra kết nối với Kafka broker
2. ✓ Tạo test topic
3. ✓ Test Producer (không cần group.id)
4. ✓ Test Consumer (cần group.id)
5. ✓ Verify Consumer fails without group.id

**Kết quả mong đợi:** Tất cả tests PASS, xác nhận hệ thống hoạt động đúng.

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

## Sending Test Data to Kafka

A Python script is provided to populate Kafka with test interaction data.

### Setup

```bash
# Install required packages
pip install -r requirements.txt
```

### Usage

```bash
# Run the producer script
python kafka_producer.py
```

The script offers three modes:
1. **Batch mode**: Send all data once
2. **Batch with delay**: Send all data with configurable delay between messages
3. **Continuous stream**: Loop forever sending data continuously

### Example Output

```
VRecommendation Kafka Producer
Loaded 60 interactions from CSV
Connecting to Kafka broker: localhost:9092
Sending 60 messages to Kafka topic 'interactions'...

SUCCESS: Message delivered to interactions [0] at offset 0
SUCCESS: Message delivered to interactions [0] at offset 1
Progress: 10/60 messages sent
...

SUMMARY:
  Total messages: 60
  Successful: 60
  Failed: 0
```

### Consuming Messages

After sending data, verify messages in Kafka:

```bash
# Using Kafka console consumer
docker exec -it test_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --from-beginning

# Or use Kafka UI at http://localhost:8080
```

### Integration with VRecommendation

Create a Data Chef to consume from Kafka:

```bash
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_messaging_queue \
  -H "Content-Type: application/json" \
  -d '{
    "name": "kafka_test_data",
    "brokers": "localhost:9092",
    "topic": "interactions",
    "group_id": "vrecom_consumer",
    "rename_columns": ""
  }'
```

Then use this data chef for model training:

```bash
curl -X POST http://localhost:9999/api/v1/add_model_task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "kafka_training",
    "model_id": "kafka_model",
    "interactions_data_chef_id": "kafka_test_data",
    "interval": 3600
  }'
```

## Notes

- This setup uses a single broker with replication factor 1, suitable for testing only
- Data persists in Docker volumes. Use `docker-compose down -v` to remove all data
- Kafka UI provides a web interface for easier topic and message management
- This is completely isolated from the main VRecom project
- The producer script reads data from `../test-data/interactions.csv`
