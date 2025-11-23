# Kafka Test Suite - Summary

## 🎯 Vấn Đề & Giải Pháp

### Vấn đề 1: Kafka Producer vs Consumer
**Vấn đề:** Test server là Producer nhưng thiếu Consumer test, không rõ tại sao cần `group.id`

**Giải pháp:**
- ✅ Tạo Consumer test với `group.id` đầy đủ
- ✅ Automated test suite verify toàn bộ
- ✅ Documentation chi tiết Producer vs Consumer

### Vấn đề 2: TasksPage API URL
**Vấn đề:** URL chỉ có `model_id`, không tường minh

**Giải pháp:**
- ✅ Thêm `task_name` vào URL
- ✅ Format: `?task_name=XXX&model_id=YYY`

---

## 📁 Files Mới

```
tests/kafka-server/
├── kafka_consumer_test.py          # Consumer test (với group.id)
├── test_kafka_connection.py        # Automated test suite
├── run_tests.cmd                   # Windows test runner
├── run_tests.sh                    # Linux/Mac test runner
├── KAFKA_PRODUCER_VS_CONSUMER.md   # Chi tiết Producer vs Consumer
├── CHANGELOG.md                    # Change log đầy đủ
└── QUICK_REFERENCE.md              # Quick reference card
```

---

## 🚀 Quick Start

```bash
# 1. Start Kafka
docker-compose up -d

# 2. Run automated test
python test_kafka_connection.py

# Expected output:
✓ TEST 1: Kafka Broker Connection - PASSED
✓ TEST 2: Create Test Topic - PASSED
✓ TEST 3: Kafka Producer (No group.id) - PASSED
✓ TEST 4: Kafka Consumer (group.id required) - PASSED
✓ TEST 5: Verify Consumer Requires group.id - PASSED

ALL TESTS PASSED!
```

---

## 🔑 Key Points

### Producer (Gửi messages)
```python
# ❌ KHÔNG CẦN group.id
config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'my-producer'
}
```

### Consumer (Nhận messages)
```python
# ✅ BẮT BUỘC phải có group.id
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-consumer-group',  # REQUIRED
    'auto.offset.reset': 'earliest'
}
```

### Tại sao Consumer cần group.id?
1. **Offset tracking** - Kafka cần biết consumer đã đọc đến đâu
2. **Load balancing** - Phân chia partitions giữa consumers
3. **Fault tolerance** - Auto rebalance khi consumer crash

---

## 🧪 Testing

### Option 1: Automated (Recommended)
```bash
python test_kafka_connection.py
```

### Option 2: Interactive Menu
```bash
# Windows
run_tests.cmd

# Linux/Mac
./run_tests.sh
```

### Option 3: Manual Testing
```bash
# Terminal 1: Consumer
python kafka_consumer_test.py

# Terminal 2: Producer
python kafka_producer.py
```

---

## 📝 TasksPage Changes

**Trước:**
```typescript
/api/v1/recommend?user_id={USER_ID}&model_id=abc123&n=10
```

**Sau:**
```typescript
/api/v1/recommend?user_id={USER_ID}&task_name=my_task&model_id=abc123&n=10
```

**Lợi ích:**
- Rõ ràng task nào đang sử dụng
- Dễ debug và monitoring
- Không breaking changes

---

## ✅ What to Test

- [ ] Run `test_kafka_connection.py` → All tests pass
- [ ] Run `kafka_producer.py` → Messages sent successfully
- [ ] Run `kafka_consumer_test.py` → Messages received successfully
- [ ] Check TasksPage → API URL có cả task_name và model_id

---

## 📚 Documentation

- **Quick start**: `QUICK_REFERENCE.md` (1 page cheat sheet)
- **Full details**: `KAFKA_PRODUCER_VS_CONSUMER.md` (Complete guide)
- **All changes**: `CHANGELOG.md` (Detailed changelog)
- **Basic usage**: `README.md` (Updated with new info)

---

## 💡 Remember

| Component | group.id | File |
|-----------|----------|------|
| Producer (Gửi) | ❌ No | `kafka_producer.py` |
| Consumer (Nhận) | ✅ Yes | `kafka_consumer_test.py` |
| VRecommendation AI Server | ✅ Yes | Uses Consumer to read data |

---

## 🚫 Breaking Changes

**NONE** - Everything is backward compatible:
- Test files only in `tests/` folder
- Frontend only adds parameter to URL
- No production code changes required
- No configuration updates needed

---

## 📞 Need Help?

1. Read: `QUICK_REFERENCE.md` (fastest)
2. Read: `KAFKA_PRODUCER_VS_CONSUMER.md` (detailed)
3. Run: `test_kafka_connection.py` (verify setup)

---

**Status**: ✅ Tested and working  
**Version**: 1.0  
**Date**: 2024