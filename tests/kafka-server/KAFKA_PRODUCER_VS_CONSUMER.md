# Kafka Producer vs Consumer: Hiểu về group.id

## Tổng quan

Tài liệu này giải thích sự khác biệt giữa **Kafka Producer** và **Kafka Consumer**, đặc biệt là tại sao Consumer cần `group.id` trong khi Producer thì không.

---

## 📤 Kafka Producer (Người gửi)

### Định nghĩa
Producer là thành phần **GỬI** (publish) messages vào Kafka topics.

### Vai trò
- Tạo và gửi dữ liệu vào Kafka topics
- Không quan tâm ai sẽ đọc messages
- Không cần theo dõi offset (vị trí đọc)
- Fire-and-forget hoặc đợi confirmation

### Configuration cơ bản

```python
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'my-producer',           # Optional: định danh producer
    'acks': 'all',                        # Optional: độ tin cậy
    'compression.type': 'gzip'            # Optional: nén dữ liệu
}
# ❌ KHÔNG CẦN group.id
```

### Tại sao Producer KHÔNG cần group.id?

1. **Không đọc dữ liệu**: Producer chỉ ghi, không đọc → không cần quản lý offset
2. **Không có consumer group**: Producer hoạt động độc lập, không cần phối hợp với ai
3. **Không có state**: Producer không cần nhớ "đã gửi đến đâu rồi"
4. **Stateless**: Mỗi message gửi đi là một operation độc lập

### Ví dụ Producer

```python
from confluent_kafka import Producer

# Tạo Producer - KHÔNG CẦN group.id
config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'test-producer'
}
producer = Producer(config)

# Gửi message
producer.produce(
    topic='interactions',
    key='user_123',
    value='{"user_id": "123", "item_id": "456", "rating": 5.0}'
)
producer.flush()
```

---

## 📥 Kafka Consumer (Người nhận)

### Định nghĩa
Consumer là thành phần **NHẬN** (subscribe) và xử lý messages từ Kafka topics.

### Vai trò
- Đọc messages từ Kafka topics
- Theo dõi offset (vị trí đã đọc đến đâu)
- Phối hợp với các consumers khác trong cùng group
- Commit offset để nhớ vị trí đã xử lý

### Configuration cơ bản

```python
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-consumer-group',      # ✅ BẮT BUỘC
    'auto.offset.reset': 'earliest',       # Đọc từ đầu nếu chưa có offset
    'enable.auto.commit': True             # Tự động commit offset
}
```

### Tại sao Consumer CẦN group.id?

#### 1. **Quản lý Offset (Vị trí đọc)**

```
Topic: interactions
Partitions: [0, 1, 2]

Offset tracking:
┌─────────────────────────────────────┐
│ Group: vrecom-consumer-group        │
│   Partition 0: offset 1500          │ ← Đã đọc đến message thứ 1500
│   Partition 1: offset 2300          │ ← Đã đọc đến message thứ 2300
│   Partition 2: offset 1800          │ ← Đã đọc đến message thứ 1800
└─────────────────────────────────────┘
```

Kafka lưu offset cho **từng group.id**. Nếu không có group.id:
- ❌ Kafka không biết lưu offset ở đâu
- ❌ Consumer sẽ đọc lại toàn bộ messages mỗi lần restart
- ❌ Không thể tiếp tục từ vị trí đã dừng

#### 2. **Load Balancing (Phân tải)**

Khi có nhiều consumers trong cùng một group:

```
Topic: interactions (3 partitions)
Group: vrecom-consumer-group

┌─────────────────────────────────────────────┐
│ Consumer 1 → Partition 0                    │
│ Consumer 2 → Partition 1                    │
│ Consumer 3 → Partition 2                    │
└─────────────────────────────────────────────┘
```

- Kafka tự động phân chia partitions cho các consumers
- Mỗi partition chỉ được đọc bởi 1 consumer trong group
- Nếu consumer chết → partition được gán lại cho consumer khác

#### 3. **Parallel Processing (Xử lý song song)**

```
Scenario: Xử lý 1 triệu messages

Không có group (1 consumer):
│████████████████████████│ 60 phút

Có group (3 consumers):
│████████│ 20 phút  (Consumer 1 - Partition 0)
│████████│ 20 phút  (Consumer 2 - Partition 1)
│████████│ 20 phút  (Consumer 3 - Partition 2)
```

#### 4. **Fault Tolerance (Chịu lỗi)**

```
Ban đầu:
Consumer 1 (P0, P1) ✓
Consumer 2 (P2, P3) ✓

Consumer 1 crashed ✗

Kafka tự động rebalance:
Consumer 2 (P0, P1, P2, P3) ✓
→ Không mất dữ liệu
→ Tiếp tục từ offset đã commit
```

### Ví dụ Consumer

```python
from confluent_kafka import Consumer

# Tạo Consumer - BẮT BUỘC phải có group.id
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'vrecom-consumer-group',  # ✅ REQUIRED
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(config)
consumer.subscribe(['interactions'])

# Đọc messages
while True:
    msg = consumer.poll(timeout=1.0)
    if msg is not None:
        print(f"Received: {msg.value()}")
```

---

## 📊 Bảng So Sánh

| Tiêu chí | Producer | Consumer |
|----------|----------|----------|
| **Chức năng** | Gửi messages | Nhận messages |
| **group.id** | ❌ Không cần | ✅ BẮT BUỘC |
| **Offset tracking** | Không | Có |
| **Load balancing** | Không | Có (trong group) |
| **State management** | Stateless | Stateful |
| **Coordination** | Không cần | Cần (với consumers khác) |
| **Config quan trọng** | `bootstrap.servers`, `client.id` | `bootstrap.servers`, `group.id`, `auto.offset.reset` |

---

## 🎯 Trong Hệ Thống VRecommendation

### Backend Application (Producer)
```python
# Backend gửi interaction events vào Kafka
producer_config = {
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'vrecom-backend'
    # ❌ Không cần group.id
}
producer.produce('interactions', user_interaction_data)
```

### AI Server (Consumer)
```python
# AI Server đọc interactions để training model
consumer_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'vrecom-ai-training-group',  # ✅ BẮT BUỘC
    'auto.offset.reset': 'earliest'
}
consumer.subscribe(['interactions'])
# Đọc data để train recommendation model
```

---

## ❓ FAQ

### Q1: Có thể dùng nhiều consumers với cùng group.id không?
**A:** Có! Đó là mục đích của consumer group. Kafka sẽ tự động phân chia partitions cho các consumers.

```
group.id = "vrecom-group"
Consumer 1 ─┐
Consumer 2 ─┼─→ Kafka tự động phân chia partitions
Consumer 3 ─┘
```

### Q2: Nhiều consumers với khác group.id thì sao?
**A:** Mỗi group nhận được TẤT CẢ messages độc lập.

```
Topic: interactions

Group A (AI Training)    → Nhận tất cả messages
Group B (Analytics)      → Nhận tất cả messages  
Group C (Backup)         → Nhận tất cả messages
```

### Q3: Test server trong folder test là Producer hay Consumer?
**A:** 
- `kafka_producer.py` → **Producer** → ❌ Không cần group.id
- `kafka_consumer_test.py` → **Consumer** → ✅ Cần group.id

### Q4: VRecommendation AI Server là Producer hay Consumer?
**A:** **Consumer** → Nhận dữ liệu từ Kafka để training model → ✅ Cần group.id

### Q5: Nếu không set group.id cho Consumer sẽ thế nào?
**A:** Kafka sẽ báo lỗi:
```
KafkaException: KafkaError{code=_INVALID_ARG,val=-186,str="group.id not configured"}
```

---

## 🚀 Best Practices

### Producer Best Practices
```python
producer_config = {
    'bootstrap.servers': 'kafka:9092',
    'client.id': 'my-app-producer',       # Giúp debug
    'acks': 'all',                        # Đảm bảo message được lưu
    'retries': 3,                         # Retry nếu fail
    'compression.type': 'gzip'            # Giảm bandwidth
}
```

### Consumer Best Practices
```python
consumer_config = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my-app-consumer-group',  # ✅ Tên có ý nghĩa
    'auto.offset.reset': 'earliest',      # Hoặc 'latest'
    'enable.auto.commit': False,          # Manual commit tốt hơn
    'max.poll.records': 100,              # Giới hạn messages/poll
    'session.timeout.ms': 30000           # Timeout detection
}

# Manual commit sau khi xử lý xong
consumer.commit()
```

### Group ID Naming Convention
```
✅ Good:
- vrecom-ai-training-group
- analytics-processor-group
- backup-consumer-group

❌ Bad:
- test
- group1
- my-consumer
```

---

## 🔧 Troubleshooting

### Lỗi: "group.id not configured"
```python
# ❌ Sai
consumer = Consumer({'bootstrap.servers': 'localhost:9092'})

# ✅ Đúng
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-group'
})
```

### Consumer không nhận được messages mới
```python
# Kiểm tra offset
'auto.offset.reset': 'latest'  # Chỉ đọc messages mới
# hoặc
'auto.offset.reset': 'earliest'  # Đọc từ đầu
```

### Messages bị xử lý nhiều lần
```python
# Sử dụng manual commit
config = {
    'enable.auto.commit': False
}
# Commit sau khi xử lý xong
process_message(msg)
consumer.commit()
```

---

## 📚 Tài Liệu Tham Khảo

- [Confluent Kafka Python Documentation](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Apache Kafka Consumer Groups](https://kafka.apache.org/documentation/#consumerconfigs)
- [VRecommendation Data Chef Service](../../backend/ai_server/src/ai_server/services/data_chef_service.py)

---

## ✅ Tóm Tắt

1. **Producer GỬI messages** → ❌ Không cần `group.id`
2. **Consumer NHẬN messages** → ✅ BẮT BUỘC phải có `group.id`
3. `group.id` giúp:
   - Quản lý offset (vị trí đọc)
   - Load balancing (phân tải)
   - Fault tolerance (chịu lỗi)
   - Parallel processing (xử lý song song)
4. Test files trong `tests/kafka-server/`:
   - `kafka_producer.py` → Producer (không cần group.id)
   - `kafka_consumer_test.py` → Consumer (cần group.id)
5. VRecommendation AI Server hoạt động như **Consumer** → cần `group.id`

---

**Lưu ý cuối:** Đừng bao giờ quên set `group.id` cho Consumer! 🚨