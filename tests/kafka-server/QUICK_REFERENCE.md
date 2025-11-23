# Kafka Testing Quick Reference Card

## 🚀 Quick Start (30 seconds)

```bash
# Start Kafka
docker-compose up -d

# Run full test
python test_kafka_connection.py
```

---

## 📋 Essential Commands

### Start/Stop Kafka
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Stop and remove data
docker-compose down -v

# View logs
docker-compose logs -f kafka
```

### Run Tests
```bash
# Automated full test
python test_kafka_connection.py

# Producer test
python kafka_producer.py

# Consumer test
python kafka_consumer_test.py

# Interactive menu (Windows)
run_tests.cmd

# Interactive menu (Linux/Mac)
./run_tests.sh

# Generate training data (RECOMMENDED for model training)
python generate_training_data.py
```

---

## 📊 Generate Training Data

### Quick Generate (for model training)
```bash
# Generate large realistic dataset
python generate_training_data.py
# Config: 200 users, 500 items, 10000 interactions
# Output: Send to Kafka (option 3)
```

### Producer with Synthetic Data
```bash
python kafka_producer.py
# Choose: Generate synthetic data (option 2)
# Count: 5000+ interactions
```

### Data Options Comparison
| Script | Users | Items | Interactions | Use Case |
|--------|-------|-------|--------------|----------|
| `test_kafka_connection.py` | 20 | 50 | 100 | Quick test |
| `kafka_producer.py` | 100 | 200 | 1000-10000 | Medium test |
| `generate_training_data.py` | **Configurable** | **Configurable** | **10000-100000+** | **Production** |

---

## 🔑 Key Concepts

### Producer (Sender)
```python
# Configuration - NO group.id needed
config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'my-producer'
}
```
- ❌ Does NOT need `group.id`
- 📤 Only sends messages
- ⚡ Stateless

### Consumer (Receiver)
```python
# Configuration - group.id REQUIRED
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-consumer-group',  # ✅ REQUIRED
    'auto.offset.reset': 'earliest'
}
```
- ✅ MUST have `group.id`
- 📥 Receives messages
- 💾 Stateful (tracks offset)

---

## 📊 Producer vs Consumer

| Feature | Producer | Consumer |
|---------|----------|----------|
| **group.id** | ❌ No | ✅ Yes |
| **Reads data** | ❌ No | ✅ Yes |
| **Writes data** | ✅ Yes | ❌ No |
| **Tracks offset** | ❌ No | ✅ Yes |
| **File** | `kafka_producer.py` | `kafka_consumer_test.py` |

---

## 🎯 Common Workflows

### Test Full System
```bash
cd tests/kafka-server
docker-compose up -d
python test_kafka_connection.py
# Expected: ALL TESTS PASSED!
```

### Manual Producer-Consumer Test
```bash
# Terminal 1: Start consumer
python kafka_consumer_test.py
# → Select mode 3 (continuous)

# Terminal 2: Start producer
python kafka_producer.py
# → Select mode 1 (batch)

# Result: Consumer receives all messages
```

### Debug Connection Issue
```bash
# 1. Check Kafka is running
docker ps | grep kafka

# 2. Check port 9092
netstat -an | grep 9092

# 3. Test connection
python test_kafka_connection.py
```

---

## 🔧 Quick Fixes

### Error: "group.id not configured"
```python
# ❌ Wrong (Consumer without group.id)
consumer = Consumer({'bootstrap.servers': 'localhost:9092'})

# ✅ Correct
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-group'
})
```

### Consumer not receiving messages
```python
# Check offset reset
'auto.offset.reset': 'earliest'  # Read from beginning
# or
'auto.offset.reset': 'latest'     # Only new messages
```

### Port 9092 already in use
```bash
# Find process using port
netstat -ano | findstr :9092  # Windows
lsof -i :9092                 # Linux/Mac

# Kill Kafka containers
docker-compose down
```

---

## 📍 Access Points

- **Kafka Broker**: `localhost:9092`
- **Kafka UI**: http://localhost:8080
- **Zookeeper**: `localhost:2181`

---

## 📝 One-Liners

```bash
# Check if Kafka is running
docker ps | grep kafka

# View Kafka logs
docker logs test_kafka -f

# List topics
docker exec test_kafka kafka-topics --list --bootstrap-server localhost:9092

# Create topic
docker exec test_kafka kafka-topics --create --topic test --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# Delete topic
docker exec test_kafka kafka-topics --delete --topic test --bootstrap-server localhost:9092

# Install dependencies
pip install -r requirements.txt

# Quick test everything
docker-compose up -d && sleep 5 && python test_kafka_connection.py

# Generate 50k training interactions
python generate_training_data.py
# → 500 users, 1000 items, 50000 interactions, Send to Kafka
```

---

## 🚀 Model Training Workflow

```bash
# Complete workflow for training models
# 1. Start Kafka
docker-compose up -d

# 2. Generate large training dataset
python generate_training_data.py
# Input: 500 users, 1000 items, 50000 interactions
# Output: Send to Kafka

# 3. Verify data
python kafka_consumer_test.py
# Mode 2: Consume limited messages to verify

# 4. Train model (use VRecommendation)
# Model will have rich data for learning patterns
```

---

## 🎓 Remember

1. **Producer**: Gửi data → ❌ No group.id
2. **Consumer**: Nhận data → ✅ MUST have group.id
3. **group.id**: Để Kafka track offset và load balance
4. **Test files**: Chỉ trong `tests/` folder, không ảnh hưởng production
5. **Training data**: Use `generate_training_data.py` cho production training (20k+ interactions)

---

## 📚 More Info

- Full docs: `README.md`
- Detailed guide: `KAFKA_PRODUCER_VS_CONSUMER.md`
- Training data: `generate_training_data.py` ⭐ (for model training)
- Changes: `CHANGELOG.md`
- Scripts: `run_tests.cmd` / `run_tests.sh`

---

## ⚡ Emergency Commands

```bash
# Everything is broken, restart fresh
docker-compose down -v
docker-compose up -d
sleep 5
python test_kafka_connection.py

# Still broken? Check Docker
docker ps
docker logs test_kafka

# Nuclear option (WARNING: deletes all data)
docker-compose down -v
docker system prune -a
docker-compose up -d
```

---

**Last updated**: 2024
**Version**: 1.0
**Status**: ✅ Tested and working