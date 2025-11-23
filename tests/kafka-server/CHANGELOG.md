# Changelog - Kafka Server Test Updates

## 📅 Ngày cập nhật: 2024

## 🎯 Mục đích

Giải quyết hai vấn đề chính:

1. **Vấn đề Kafka Connection**: Làm rõ sự khác biệt giữa Producer và Consumer, đặc biệt là tại sao Consumer cần `group.id` trong khi Producer thì không.

2. **Vấn đề API URL trong TasksPage**: Sửa URL recommendation API để sử dụng task name thay vì model_id, làm cho API endpoint tường minh hơn về mục đích sử dụng.

---

## ✨ Các File Mới Được Tạo

### 1. `kafka_consumer_test.py`
**Consumer test script với group.id đầy đủ**

- ✅ Implement Kafka Consumer với configuration đúng chuẩn
- ✅ Bao gồm `group.id` (BẮT BUỘC cho Consumer)
- ✅ Hỗ trợ nhiều modes: test connection, consume limited, continuous
- ✅ Hiển thị chi tiết messages nhận được
- ✅ Xử lý errors và timeouts gracefully

**Sử dụng:**
```bash
python kafka_consumer_test.py
```

### 2. `test_kafka_connection.py`
**Script test tổng hợp và tự động**

- ✅ Test broker connection
- ✅ Test Producer (verify không cần group.id)
- ✅ Test Consumer (verify cần group.id)
- ✅ Verify Consumer fails without group.id
- ✅ Tạo và test với test topic riêng
- ✅ Báo cáo kết quả chi tiết

**Sử dụng:**
```bash
python test_kafka_connection.py
```

### 3. `run_tests.sh` (Linux/Mac)
**Menu-driven test runner script**

- ✅ Start/Stop Kafka server
- ✅ Show status và logs
- ✅ Run các test scripts
- ✅ Check dependencies tự động
- ✅ Open Kafka UI
- ✅ Color-coded output

**Sử dụng:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### 4. `run_tests.cmd` (Windows)
**Windows batch script tương tự run_tests.sh**

- ✅ Menu interface giống Linux version
- ✅ Color support cho Windows
- ✅ Tất cả features của Linux version

**Sử dụng:**
```cmd
run_tests.cmd
```

### 5. `KAFKA_PRODUCER_VS_CONSUMER.md`
**Tài liệu chi tiết giải thích Producer vs Consumer**

Nội dung bao gồm:
- 📤 Producer: Định nghĩa, vai trò, configuration
- 📥 Consumer: Định nghĩa, vai trò, configuration
- 🔍 Tại sao Producer KHÔNG cần group.id
- 🔍 Tại sao Consumer CẦN group.id
- 📊 Bảng so sánh chi tiết
- 🎯 Áp dụng trong VRecommendation
- ❓ FAQ
- 🚀 Best practices
- 🔧 Troubleshooting

---

## 📝 Các File Được Cập Nhật

### 1. `README.md`
**Thêm documentation về test scripts**

Cập nhật:
- ✅ Thêm mô tả về `kafka_producer.py` và `kafka_consumer_test.py`
- ✅ Giải thích sự khác biệt giữa Producer và Consumer
- ✅ Configuration examples cho cả Producer và Consumer
- ✅ Workflow test hoàn chỉnh
- ✅ Hướng dẫn sử dụng test runner scripts
- ✅ Quick start guide với automated tests
- ✅ Bảng so sánh Producer vs Consumer

### 2. `frontend/project/src/components/TasksPage.tsx`
**Sửa API URL để tường minh hơn**

**Trước đây:**
```typescript
const getRecommendUrl = (modelId: string) => {
    return `${apiUrl}/api/v1/recommend?user_id={USER_ID}&model_id=${modelId}&n=10`;
};
```

**Bây giờ:**
```typescript
const getRecommendUrl = (taskName: string, modelId: string) => {
    return `${apiUrl}/api/v1/recommend?user_id={USER_ID}&task_name=${taskName}&model_id=${modelId}&n=10`;
};
```

**Lợi ích:**
- ✅ URL rõ ràng hơn về task đang sử dụng
- ✅ Dễ debug và tracking
- ✅ Tường minh về mục đích sử dụng API
- ✅ Không phá vỡ code hiện tại

---

## 🔑 Điểm Quan Trọng

### Producer vs Consumer

| Aspect | Producer | Consumer |
|--------|----------|----------|
| **Vai trò** | Gửi messages | Nhận messages |
| **group.id** | ❌ KHÔNG CẦN | ✅ BẮT BUỘC |
| **Lý do** | Không cần quản lý offset | Cần track vị trí đã đọc |
| **File test** | `kafka_producer.py` | `kafka_consumer_test.py` |

### Tại sao Consumer cần group.id?

1. **Offset Management**: Kafka cần biết consumer đã đọc đến đâu
2. **Load Balancing**: Phân phối partitions giữa các consumers
3. **Fault Tolerance**: Tự động rebalance khi consumer crash
4. **Parallel Processing**: Nhiều consumers xử lý song song

### VRecommendation System

```
Backend App (Producer) → Kafka → AI Server (Consumer)
      ❌ No group.id              ✅ Has group.id
```

- Backend gửi interaction events (Producer)
- AI Server nhận data để training (Consumer)

---

## 🚀 Hướng Dẫn Sử Dụng

### Quick Start

```bash
# 1. Start Kafka
docker-compose up -d

# 2. Run automated test
python test_kafka_connection.py

# 3. Test Producer (terminal 1)
python kafka_producer.py

# 4. Test Consumer (terminal 2)
python kafka_consumer_test.py
```

### Sử dụng Test Runner

**Windows:**
```cmd
run_tests.cmd
```

**Linux/Mac:**
```bash
./run_tests.sh
```

Menu options:
1. Start Kafka Server
2. Stop Kafka Server
3. Show Status
4. Show Logs
5. **Run Connection Test** ← Recommended để verify toàn bộ
6. Run Producer Test
7. Run Consumer Test
8. Open Kafka UI
9. Exit

---

## 🧪 Testing Workflow

### Workflow Đầy Đủ

```bash
# Bước 1: Start Kafka
cd tests/kafka-server
docker-compose up -d

# Bước 2: Install dependencies
pip install -r requirements.txt

# Bước 3: Run full test suite
python test_kafka_connection.py
# → Kiểm tra tất cả: connection, producer, consumer, group.id

# Bước 4: (Optional) Manual testing
# Terminal 1:
python kafka_consumer_test.py
# Chọn mode 3 (continuous)

# Terminal 2:
python kafka_producer.py
# Chọn mode 1 (batch)
```

### Kết Quả Mong Đợi

```
✓ TEST 1: Kafka Broker Connection - PASSED
✓ TEST 2: Create Test Topic - PASSED
✓ TEST 3: Kafka Producer (No group.id) - PASSED
✓ TEST 4: Kafka Consumer (group.id required) - PASSED
✓ TEST 5: Verify Consumer Requires group.id - PASSED

ALL TESTS PASSED!
```

---

## 📚 Tài Liệu Tham Khảo

- `README.md` - Overview và basic usage
- `KAFKA_PRODUCER_VS_CONSUMER.md` - Chi tiết về Producer vs Consumer
- `kafka_producer.py` - Producer implementation
- `kafka_consumer_test.py` - Consumer implementation
- `test_kafka_connection.py` - Automated test suite

---

## 🐛 Troubleshooting

### Consumer không nhận messages

**Nguyên nhân:** Thiếu hoặc sai `group.id`

**Giải pháp:**
```python
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-consumer-group',  # ✅ Thêm dòng này
    'auto.offset.reset': 'earliest'
}
```

### Producer gặp lỗi group.id

**Nguyên nhân:** Nhầm lẫn giữa Producer và Consumer

**Giải pháp:**
```python
# Producer không cần group.id
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'my-producer'
    # ❌ Không thêm group.id
}
```

### Test connection failed

**Kiểm tra:**
1. Kafka có chạy không? → `docker ps | grep kafka`
2. Port 9092 có available không?
3. Dependencies đã cài chưa? → `pip install confluent-kafka`

---

## ✅ Checklist Sau Khi Update

- [x] Kafka Producer hoạt động (không cần group.id)
- [x] Kafka Consumer hoạt động (với group.id)
- [x] Test scripts chạy thành công
- [x] Documentation đầy đủ
- [x] TasksPage API URL đã được cập nhật
- [x] Test runner scripts hoạt động
- [x] Automated tests pass

---

## 💡 Lưu Ý Quan Trọng

1. **Producer ≠ Consumer**: Đừng nhầm lẫn configuration của hai loại client
2. **group.id là BẮT BUỘC**: Cho Consumer, không có thương lượng
3. **Test trước khi deploy**: Luôn chạy `test_kafka_connection.py` trước
4. **Files trong test folder**: Chỉ để test, không ảnh hưởng production code

---

## 🎉 Tóm Tắt

Update này giải quyết:
1. ✅ Làm rõ sự khác biệt Producer vs Consumer
2. ✅ Cung cấp Consumer test đầy đủ với group.id
3. ✅ Automated test suite để verify toàn bộ
4. ✅ Test runner scripts tiện lợi
5. ✅ Documentation chi tiết
6. ✅ API URL trong TasksPage tường minh hơn

**Kết quả:** Hệ thống test Kafka hoàn chỉnh, dễ hiểu, dễ sử dụng! 🚀