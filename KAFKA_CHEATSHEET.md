# 🚀 Kafka Cheat Sheet - VRecommendation

## 📦 Docker Commands

### Start/Stop Services
```bash
# Start tất cả services
docker-compose up -d

# Start chỉ Kafka và Zookeeper
docker-compose up -d zookeeper kafka

# Stop tất cả
docker-compose down

# Stop và xóa volumes
docker-compose down -v

# Restart Kafka
docker-compose restart kafka

# View logs
docker-compose logs -f kafka
docker-compose logs -f zookeeper
```

### Container Management
```bash
# Check status
docker-compose ps

# Access Kafka container
docker exec -it vrecom_kafka bash

# Access Zookeeper container
docker exec -it vrecom_zookeeper bash
```

---

## 📋 Kafka Topics

### List Topics
```bash
# List all topics
docker exec vrecom_kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe all topics
docker exec vrecom_kafka kafka-topics --describe --bootstrap-server localhost:9092

# Describe specific topic
docker exec vrecom_kafka kafka-topics --describe --topic interactions --bootstrap-server localhost:9092
```

### Create Topic
```bash
# Create topic with 3 partitions, replication 1
docker exec vrecom_kafka kafka-topics --create \
  --topic interactions \
  --partitions 3 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

# Create topic with custom config
docker exec vrecom_kafka kafka-topics --create \
  --topic events \
  --partitions 5 \
  --replication-factor 1 \
  --config retention.ms=86400000 \
  --bootstrap-server localhost:9092
```

### Delete Topic
```bash
# Delete topic
docker exec vrecom_kafka kafka-topics --delete \
  --topic test_topic \
  --bootstrap-server localhost:9092
```

### Alter Topic
```bash
# Increase partitions (cannot decrease)
docker exec vrecom_kafka kafka-topics --alter \
  --topic interactions \
  --partitions 5 \
  --bootstrap-server localhost:9092

# Update topic config
docker exec vrecom_kafka kafka-configs --alter \
  --entity-type topics \
  --entity-name interactions \
  --add-config retention.ms=604800000 \
  --bootstrap-server localhost:9092
```

---

## 📤 Producer Commands

### Console Producer
```bash
# Start console producer
docker exec -it vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic interactions

# Then type messages (JSON format):
{"user_id":"user1","item_id":"item1","action":"view","timestamp":"2025-01-23T10:00:00"}
{"user_id":"user2","item_id":"item2","action":"purchase","timestamp":"2025-01-23T10:01:00"}
# Press Ctrl+C to exit
```

### Producer with Key
```bash
docker exec -it vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --property "parse.key=true" \
  --property "key.separator=:"

# Format: key:value
user1:{"item_id":"item1","action":"view"}
```

### Producer from File
```bash
# From Windows
type data.json | docker exec -i vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic interactions

# From Linux/Mac
cat data.json | docker exec -i vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic interactions
```

---

## 📥 Consumer Commands

### Console Consumer
```bash
# Consume from beginning
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --from-beginning

# Consume only new messages
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions

# Consume with group
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --group my-consumer-group \
  --from-beginning
```

### Consumer with Formatting
```bash
# Show key and value
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --property print.key=true \
  --property key.separator=" : " \
  --from-beginning

# Show timestamp
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --property print.timestamp=true \
  --from-beginning
```

### Consumer with Offset
```bash
# Consume from specific partition and offset
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --partition 0 \
  --offset 10

# Consume last N messages (example: last 100)
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --partition 0 \
  --offset latest \
  --max-messages 100
```

---

## 👥 Consumer Groups

### List Consumer Groups
```bash
# List all consumer groups
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Describe specific group
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --describe
```

### Reset Consumer Group Offset
```bash
# Reset to earliest
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --reset-offsets \
  --to-earliest \
  --all-topics \
  --execute

# Reset to latest
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --reset-offsets \
  --to-latest \
  --all-topics \
  --execute

# Reset to specific offset
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --reset-offsets \
  --to-offset 100 \
  --topic interactions \
  --execute

# Reset by datetime
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --reset-offsets \
  --to-datetime 2025-01-23T10:00:00.000 \
  --all-topics \
  --execute
```

### Delete Consumer Group
```bash
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group old_group \
  --delete
```

---

## 🔍 Monitoring & Debugging

### Broker Information
```bash
# List brokers
docker exec vrecom_kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# Cluster info
docker exec vrecom_kafka kafka-metadata --bootstrap-server localhost:9092 --describe
```

### Topic Details
```bash
# Get topic size
docker exec vrecom_kafka kafka-log-dirs \
  --bootstrap-server localhost:9092 \
  --describe --topic-list interactions

# Get topic configuration
docker exec vrecom_kafka kafka-configs \
  --bootstrap-server localhost:9092 \
  --entity-type topics \
  --entity-name interactions \
  --describe
```

### Check Partition Lag
```bash
# Check consumer lag
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group vrecom_ai_server_group \
  --describe

# Output shows: TOPIC, PARTITION, CURRENT-OFFSET, LOG-END-OFFSET, LAG
```

### Performance Testing
```bash
# Producer performance test
docker exec vrecom_kafka kafka-producer-perf-test \
  --topic test_perf \
  --num-records 10000 \
  --record-size 1000 \
  --throughput -1 \
  --producer-props bootstrap.servers=localhost:9092

# Consumer performance test
docker exec vrecom_kafka kafka-consumer-perf-test \
  --bootstrap-server localhost:9092 \
  --topic test_perf \
  --messages 10000
```

---

## 🛠️ Troubleshooting

### Check Connectivity
```bash
# Test connection from AI server
docker exec vrecom_ai_server nc -zv kafka 9093

# Test connection from host
telnet localhost 9092
```

### View Logs
```bash
# Kafka logs
docker-compose logs -f kafka

# Zookeeper logs
docker-compose logs -f zookeeper

# AI Server Kafka errors
docker-compose logs ai_server | grep -i kafka

# Last 100 lines
docker-compose logs --tail=100 kafka
```

### Check Disk Usage
```bash
# Check Kafka data size
docker exec vrecom_kafka du -sh /var/lib/kafka/data

# Check specific topic size
docker exec vrecom_kafka du -sh /var/lib/kafka/data/interactions-*
```

### Clean Up
```bash
# Delete all data (DANGEROUS!)
docker-compose down -v

# Delete specific topic data
docker exec vrecom_kafka kafka-topics --delete --topic old_topic --bootstrap-server localhost:9092

# Restart to clean memory
docker-compose restart kafka
```

---

## 🌐 Kafka UI (Web Interface)

```bash
# Access Kafka UI
http://localhost:8080

# Features:
- View topics and messages
- Monitor consumer groups
- Check broker status
- Create/delete topics
- View configurations
```

---

## 🐍 Python Code Examples

### Producer Example
```python
from confluent_kafka import Producer
import json

# Configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'python-producer'
}

producer = Producer(conf)

# Send message
data = {
    'user_id': 'user1',
    'item_id': 'item1',
    'action': 'view'
}
producer.produce('interactions', json.dumps(data).encode('utf-8'))
producer.flush()
```

### Consumer Example
```python
from confluent_kafka import Consumer
import json

# Configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my_group',
    'auto.offset.reset': 'earliest'
}

consumer = Consumer(conf)
consumer.subscribe(['interactions'])

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
        else:
            data = json.loads(msg.value().decode('utf-8'))
            print(f"Received: {data}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
```

---

## 🔧 Environment Variables

```env
# Docker Compose
KAFKA_PORT=9092
KAFKA_UI_PORT=8080
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_GROUP_ID=vrecom_ai_server_group

# Python Application
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_DEFAULT_TOPIC=interactions
KAFKA_GROUP_ID=vrecom_ai_server_group
```

---

## 📝 Common Use Cases

### 1. Send User Interaction Event
```bash
docker exec -it vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic interactions
  
# Enter:
{"user_id":"user123","item_id":"item456","action":"view","timestamp":"2025-01-23T12:00:00","rating":4.5}
```

### 2. Monitor Real-time Events
```bash
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic interactions \
  --property print.timestamp=true
```

### 3. Export Messages to File
```bash
# Windows
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interactions --from-beginning --max-messages 1000 > messages.json

# Linux/Mac
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interactions --from-beginning --max-messages 1000 > messages.json
```

### 4. Test AI Server Integration
```bash
# Create data chef
curl -X POST http://localhost:9999/api/v1/private/data-chef/message-queue \
  -H "Content-Type: application/json" \
  -d '{
    "data_chef_id": "kafka_interactions",
    "brokers": "kafka:9093",
    "topic": "interactions",
    "group_id": "vrecom_group",
    "rename_columns": "user_id:user_id,item_id:item_id"
  }'
```

---

## ⚡ Quick Commands

```bash
# Start everything
docker-compose up -d && sleep 15 && docker-compose ps

# Send test message
echo '{"user":"test","item":"test123","action":"view"}' | docker exec -i vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic interactions

# Read test message
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interactions --from-beginning --max-messages 1

# Check if Kafka is ready
docker exec vrecom_kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo "Kafka is ready!" || echo "Kafka is not ready"

# Full reset
docker-compose down -v && docker-compose up -d
```

---

## 🎯 Tips & Best Practices

1. **Always use `kafka:9093` trong Docker network**
2. **Use `localhost:9092` từ host machine**
3. **Set appropriate retention policy** cho production
4. **Monitor consumer lag** thường xuyên
5. **Use consumer groups** để scale horizontally
6. **Set proper replication factor** (≥3 for production)
7. **Enable auto topic creation** cho development
8. **Use Kafka UI** để debug nhanh
9. **Backup consumer offsets** trước khi reset
10. **Test với small messages** trước khi scale

---

**Version**: 1.0  
**Last Updated**: 2025-01-23  
**Documentation**: See `KAFKA_FIX_GUIDE.md` for details