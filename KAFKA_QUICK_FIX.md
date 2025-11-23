# 🚀 Kafka Connection Refused - Quick Fix

## Lỗi Gặp Phải

```
Connection refused: localhost:9092
```

## ✅ Giải Pháp Nhanh (3 Bước)

### Bước 1: Cập nhật file `.env`

Sao chép từ `example-env` hoặc thêm vào file `.env`:

```env
KAFKA_PORT=9092
KAFKA_UI_PORT=8080
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_GROUP_ID=vrecom_ai_server_group
```

### Bước 2: Khởi động lại Docker

```bash
# Dừng tất cả
docker-compose down

# Khởi động lại (Kafka đã được thêm vào docker-compose.yml)
docker-compose up -d

# Đợi 10-15 giây để Kafka khởi động
```

### Bước 3: Kiểm tra

```bash
# Xem logs để đảm bảo không còn lỗi
docker-compose logs -f ai_server

# Kiểm tra Kafka
docker ps | grep kafka

# Mở Kafka UI (nếu muốn)
# Truy cập: http://localhost:8080
```

## 🎯 Xong!

Hệ thống của bạn bây giờ đã có:
- ✅ Zookeeper (port 2181)
- ✅ Kafka (port 9092 external, 9093 internal)
- ✅ Kafka UI (port 8080)
- ✅ AI Server đã kết nối được với Kafka

## 📌 Lưu Ý

- **Trong Docker**: AI Server sử dụng `kafka:9093`
- **Từ máy local**: Các test script sử dụng `localhost:9092`
- **Kafka UI**: http://localhost:8080 để xem topics và messages

## 🐛 Nếu Vẫn Lỗi

```bash
# 1. Restart Kafka
docker-compose restart kafka zookeeper

# 2. Xem logs chi tiết
docker-compose logs kafka

# 3. Nếu vẫn không được, clean và start lại
docker-compose down -v
docker-compose up -d
```

## 💡 Test Kafka

```bash
# Test producer (gửi message)
docker exec vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic test
# Nhập: {"test": "hello"}
# Nhấn Ctrl+C

# Test consumer (đọc message)
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning
```

---

**Thời gian**: ~2 phút  
**Độ khó**: ⭐⭐☆☆☆

Xem chi tiết: `KAFKA_FIX_GUIDE.md`
