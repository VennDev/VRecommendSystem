# 🎓 Kafka Training Troubleshooting Guide

## 🐛 Vấn Đề: Model Không Học Được Dữ Liệu

### Triệu Chứng
```bash
# API trả về predictions rỗng
{"predictions":{"user_2":[]}, "status":"completed"}

# Model metadata cho thấy rất ít data
"n_users": 2,
"n_items": 3,
"n_interactions": 4
```

Mặc dù Kafka có 52+ messages nhưng model chỉ học được 4 interactions!

---

## 🔍 Nguyên Nhân

### 1. **Consumer Offset Đã Ở Cuối**
Khi AI Server khởi động, Kafka consumer đọc từ offset hiện tại (cuối topic). Nếu bạn đã generate data TRƯỚC KHI start AI server, consumer sẽ không đọc được messages cũ.

```
Timeline:
1. Generate 52 messages → Kafka   ✅
2. Start AI Server → Consumer starts at offset 52 (end)  ⚠️
3. Consumer waits for NEW messages (không đọc 52 messages cũ)  ❌
```

### 2. **Consumer Không Timeout**
Code hiện tại dùng `consumer.poll()` trong vòng lặp vô hạn:
```python
while True:
    msg = consumer.poll(1.0)  # Chờ mãi mãi!
```

Điều này khiến training task "treo" chờ messages mới.

### 3. **Data Format Không Đúng**
Một số messages không phải JSON:
```
user_id:user2 item_id:item2 rating:5  ❌ (text format)
{"user_id":"user1","item_id":"item1","rating":5}  ✅ (JSON)
```

Messages không phải JSON sẽ bị bỏ qua.

---

## ✅ Giải Pháp

### 🚀 **Quick Fix (Khuyến Nghị)**

#### Bước 1: Dừng AI Server
```bash
docker-compose stop ai_server
```

#### Bước 2: Reset Consumer Group Offset
```bash
# Chờ consumer inactive (10-15 giây)
timeout 15

# Reset offset về đầu
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group test_connection_consumer_group \
  --reset-offsets \
  --to-earliest \
  --topic test_connection_topic \
  --execute
```

**Output:**
```
GROUP                          TOPIC                 PARTITION  NEW-OFFSET
test_connection_consumer_group test_connection_topic 0          0
```

#### Bước 3: Xóa Model Cũ
```bash
docker exec vrecom_ai_server rm -f models/kafka_test*
```

#### Bước 4: Generate FRESH Data
```bash
cd tests/kafka-server
python generate_training_data.py

# Chọn option 3: Send to Kafka
# Nhập topic: test_connection_topic
# Chọn số lượng messages (recommend: 100-500)
```

#### Bước 5: Kiểm Tra Messages
```bash
# Count messages
docker exec vrecom_kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic test_connection_topic

# Output: test_connection_topic:0:502 (502 messages)

# Sample messages
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test_connection_topic \
  --from-beginning \
  --max-messages 5
```

Đảm bảo tất cả messages đều là JSON format!

#### Bước 6: Start AI Server
```bash
docker-compose start ai_server

# Đợi 10 giây để khởi động
timeout 10

# Check logs
docker-compose logs -f ai_server
```

#### Bước 7: Đợi Training Task Chạy
Training task chạy mỗi 60 giây. Hoặc trigger manually (cần auth).

**Xem logs:**
```bash
docker-compose logs --tail=200 ai_server | findstr kafka_test
```

Tìm dòng như:
```
Batch 1 processed for kafka_test (1 interactions)
Batch 2 processed for kafka_test (1 interactions)
...
Training completed successfully for kafka_test
Model kafka_test saved to models/kafka_test.pkl
```

#### Bước 8: Verify Model
```bash
# Check model metadata
docker exec vrecom_ai_server cat models/kafka_test_metadata.json

# Should see something like:
# "n_users": 20,
# "n_items": 50,
# "n_interactions": 500
```

#### Bước 9: Test Recommendations
```bash
# Replace user_1 with actual user from your data
curl "http://localhost:2030/api/v1/recommend?user_id=user_1&task_name=kafka_test&model_id=kafka_test&n=10"
```

**Expected output:**
```json
{
  "predictions": {
    "user_1": [
      {"item_id": "item_5", "score": 4.8},
      {"item_id": "item_12", "score": 4.6},
      ...
    ]
  },
  "status": "completed"
}
```

---

## 🔧 **Advanced Fixes**

### Fix 1: Change Consumer Auto Offset Reset

Edit `restaurant_data.yaml`:
```yaml
kafka_test:
    brokers: kafka:9093
    group_id: test_connection_consumer_group
    topic: test_connection_topic
    type: messaging_queue
    rename_columns: ""
    auto_offset_reset: earliest  # Add this line
```

### Fix 2: Sử dụng Unique Consumer Group

Mỗi lần train, dùng group ID khác:
```yaml
kafka_test:
    group_id: test_consumer_group_v2  # Change this
```

Consumer group mới sẽ đọc từ đầu topic.

### Fix 3: Monitor Consumer Lag

```bash
# Check consumer status
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group test_connection_consumer_group
```

**Output:**
```
GROUP                          TOPIC      PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
test_connection_consumer_group test_...   0          502             502             0
```

- **LAG = 0**: Consumer đã đọc hết, đang chờ messages mới
- **LAG > 0**: Consumer đang đọc messages cũ (good!)

---

## 📊 **Workflow Đúng**

### Scenario 1: Training Lần Đầu

```bash
# 1. Start hệ thống (KHÔNG có model)
docker-compose up -d

# 2. Generate data VÀO Kafka
cd tests/kafka-server
python generate_training_data.py
# → Send 500 messages to test_connection_topic

# 3. Đợi training task chạy (60 giây)
# HOẶC restart AI server để trigger ngay
docker-compose restart ai_server

# 4. Verify
curl "http://localhost:2030/api/v1/recommend?user_id=user_1&task_name=kafka_test&model_id=kafka_test&n=10"
```

### Scenario 2: Retrain Với Data Mới

```bash
# 1. Generate thêm data
python generate_training_data.py
# → Send 200 more messages

# 2. Đợi task chạy (auto mỗi 60s)
# Consumer sẽ đọc từ offset cuối cùng (incremental)

# 3. Model được update với data mới
```

### Scenario 3: Full Retrain Từ Đầu

```bash
# 1. Stop AI server
docker-compose stop ai_server

# 2. Reset offset
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group test_connection_consumer_group \
  --reset-offsets --to-earliest \
  --topic test_connection_topic --execute

# 3. Delete model
docker exec vrecom_ai_server rm -f models/kafka_test*

# 4. Start AI server
docker-compose start ai_server

# 5. Đợi training (60s)
```

---

## 🎯 **Best Practices**

### 1. Data Generation

**✅ DO:**
- Generate data với JSON format
- Include timestamp
- Use diverse users (10-100 users)
- Use diverse items (20-200 items)
- Generate 100-1000 interactions minimum

**❌ DON'T:**
- Generate data sau khi AI server đã chạy (sẽ bị lag)
- Use text format
- Generate quá ít data (<20 interactions)

### 2. Consumer Groups

**✅ DO:**
- Mỗi model/use case dùng group ID riêng
- Reset offset khi cần full retrain
- Monitor consumer lag thường xuyên

**❌ DON'T:**
- Dùng chung group ID cho nhiều services
- Delete consumer group khi đang active

### 3. Training

**✅ DO:**
- Verify data trong Kafka trước khi train
- Check model metadata sau training
- Test recommendations với nhiều users
- Monitor training logs

**❌ DON'T:**
- Train với quá ít data
- Ignore training errors
- Train mà không verify kết quả

---

## 🐛 **Common Issues**

### Issue 1: "predictions": []

**Cause:** User không có trong training data

**Fix:**
```bash
# List all users in data
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test_connection_topic \
  --from-beginning --max-messages 1000 | \
  grep -o '"user_id":"[^"]*"' | sort -u

# Test với user thực tế
curl "http://localhost:2030/api/v1/recommend?user_id=user_1&..."
```

### Issue 2: Model có quá ít interactions

**Cause:** Consumer offset đã ở cuối, training task chỉ đọc messages mới

**Fix:** Reset consumer offset (xem Quick Fix bước 2)

### Issue 3: Training task "treo"

**Cause:** Kafka consumer đang chờ messages mới mãi mãi

**Fix:** 
```bash
# Send một message mới để trigger
echo '{"user_id":"dummy","item_id":"dummy","rating":1}' | \
  docker exec -i vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic test_connection_topic
```

### Issue 4: Consumer lag không giảm

**Cause:** AI server không đọc messages

**Fix:**
```bash
# Check AI server logs
docker-compose logs -f ai_server

# Restart AI server
docker-compose restart ai_server
```

---

## 📈 **Monitoring**

### Check Training Progress

```bash
# Real-time logs
docker-compose logs -f ai_server | grep kafka_test

# Count batches processed
docker-compose logs ai_server | grep "Batch.*kafka_test" | wc -l
```

### Check Consumer Status

```bash
# Consumer group info
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group test_connection_consumer_group

# Topic info
docker exec vrecom_kafka kafka-topics \
  --describe --topic test_connection_topic \
  --bootstrap-server localhost:9092
```

### Check Model Status

```bash
# Model files
docker exec vrecom_ai_server ls -lh models/ | grep kafka_test

# Model metadata
docker exec vrecom_ai_server cat models/kafka_test_metadata.json | jq
```

---

## 🔗 **Useful Commands**

```bash
# Delete all messages in topic (careful!)
docker exec vrecom_kafka kafka-topics \
  --delete --topic test_connection_topic \
  --bootstrap-server localhost:9092

# Recreate topic
docker exec vrecom_kafka kafka-topics \
  --create --topic test_connection_topic \
  --partitions 3 --replication-factor 1 \
  --bootstrap-server localhost:9092

# View Kafka UI
start http://localhost:8080

# Reset everything
docker-compose down -v
docker-compose up -d
```

---

## 📚 **References**

- Main Kafka guide: `KAFKA_FIX_GUIDE.md`
- Quick fix: `KAFKA_QUICK_FIX.md`
- Commands cheatsheet: `KAFKA_CHEATSHEET.md`
- Full changelog: `CHANGELOG_KAFKA.md`

---

**Last Updated:** 2025-01-23  
**Version:** 1.0.0