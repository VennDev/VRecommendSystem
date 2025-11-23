# 🔧 Kafka Broker Configuration Fix

## ❌ Vấn Đề

Model `model_kafka` không học được data từ Kafka mặc dù đã generate dữ liệu.

### Nguyên Nhân

**File `restaurant_data.yaml` có cấu hình SAI:**
```yaml
kafka_test:
  brokers: localhost:9093  # ❌ SAI!
  type: messaging           # ❌ SAI!
```

**Giải thích:**
- `localhost:9093` - **KHÔNG TỒN TẠI** từ bên trong Docker container
- Phải dùng `kafka:9093` (Docker service name)
- Type phải là `messaging_queue` không phải `messaging`

---

## ✅ Giải Pháp

### Bước 1: Sửa Config File

**File:** `backend/ai_server/config/restaurant_data.yaml`

```yaml
kafka_test:
  brokers: kafka:9093          # ✅ ĐÚNG - Docker internal
  group_id: test_connection_consumer_group
  rename_columns: ""
  topic: test_connection_topic
  type: messaging_queue        # ✅ ĐÚNG
```

### Bước 2: Reset Consumer Offset

```bash
# Stop AI server
docker-compose stop ai_server

# Đợi consumer inactive (15 giây)
timeout 15

# Reset offset về đầu
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group test_connection_consumer_group \
  --reset-offsets --to-earliest \
  --topic test_connection_topic --execute
```

### Bước 3: Xóa Model Cũ và Restart

```bash
# Start AI server
docker-compose start ai_server

# Sau khi AI server chạy, xóa model cũ
docker exec vrecom_ai_server rm -f models/model_kafka* models/kafka_test*

# Restart để áp dụng config mới
docker-compose restart ai_server
```

### Bước 4: Đợi Training (60 giây)

```bash
# Monitor training progress
docker-compose logs -f ai_server | grep model_kafka

# Hoặc check batch progress
docker-compose logs --tail=200 ai_server | grep "Batch.*model_kafka"
```

### Bước 5: Verify Model

```bash
# Check model file
docker exec vrecom_ai_server ls -lh models/ | grep model_kafka

# Check model metadata
docker exec vrecom_ai_server cat models/model_kafka_metadata.json
```

Should see:
```json
{
  "n_users": 15+,
  "n_items": 30+,
  "n_interactions": 50+
}
```

### Bước 6: Test Recommendations

```bash
curl "http://localhost:2030/api/v1/recommend?user_id=user_1&model_id=model_kafka&n=10"
```

Expected:
```json
{
  "predictions": {
    "user_1": [
      {"item_id": "item_5", "score": 4.8},
      {"item_id": "item_12", "score": 4.6}
    ]
  },
  "status": "completed"
}
```

---

## 🎯 Port Reference

| Location | Use | Broker Address |
|----------|-----|----------------|
| **Từ máy host** (laptop/PC) | Generate data, test | `localhost:9092` |
| **Từ Docker container** (AI server) | Training, consume | `kafka:9093` |

### Ví Dụ

**Đúng:**
```bash
# Generate data từ máy host
python generate_training_data.py
# → Kết nối: localhost:9092 ✅

# AI server trong Docker
brokers: kafka:9093  ✅
```

**Sai:**
```yaml
# AI server config
brokers: localhost:9093  ❌ (không tồn tại trong container!)
brokers: localhost:9092  ❌ (external port, không access được)
```

---

## 📝 Quick Commands

```bash
# Check Kafka topics
docker exec vrecom_kafka kafka-topics --list --bootstrap-server localhost:9092

# Count messages in topic
docker exec vrecom_kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 --topic test_connection_topic

# Check consumer lag
docker exec vrecom_kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group test_connection_consumer_group

# Send test message (from host)
echo '{"user_id":"user_1","item_id":"item_5","rating":5}' | \
  docker exec -i vrecom_kafka kafka-console-producer \
  --bootstrap-server localhost:9092 --topic test_connection_topic

# View messages
docker exec vrecom_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test_connection_topic --from-beginning --max-messages 10
```

---

## ⚡ TL;DR

```bash
# 1. Sửa restaurant_data.yaml
#    localhost:9093 → kafka:9093
#    messaging → messaging_queue

# 2. Reset và restart
docker-compose stop ai_server
docker exec vrecom_kafka kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group test_connection_consumer_group --reset-offsets --to-earliest \
  --topic test_connection_topic --execute
docker-compose start ai_server

# 3. Đợi 60 giây để training chạy

# 4. Test
curl "http://localhost:2030/api/v1/recommend?user_id=user_1&model_id=model_kafka&n=10"
```

---

**Status:** ✅ FIXED  
**Updated:** 2025-01-23  
**Files Changed:** `backend/ai_server/config/restaurant_data.yaml`
