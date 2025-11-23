# Hướng Dẫn Sửa Lỗi Kafka Connection Refused

## 📋 Mô Tả Vấn Đề

Khi chạy hệ thống với Docker hoặc chạy bình thường, bạn gặp lỗi:

```
%3|1763859450.370|FAIL|rdkafka#consumer-7| [thrd:localhost:9092/bootstrap]: 
localhost:9092/bootstrap: Connect to ipv4#127.0.0.1:9092 failed: Connection refused
```

## 🔍 Nguyên Nhân

Hệ thống AI Server đang cố kết nối đến Kafka tại `localhost:9092` nhưng:
- **Khi chạy với Docker**: Không có Kafka service trong docker-compose.yml
- **Khi chạy bình thường**: Kafka service chưa được khởi động hoặc cấu hình sai địa chỉ

## ✅ Giải Pháp

Có **2 cách** để giải quyết vấn đề này:

---

## 🐳 Cách 1: Chạy Toàn Bộ Với Docker (Khuyến Nghị)

### Bước 1: Cập nhật file `.env`

Sao chép từ `example-env` và thêm cấu hình Kafka (nếu chưa có):

```env
# Kafka Configuration
KAFKA_PORT=9092
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_GROUP_ID=vrecom_ai_server_group
```

**Lưu ý**: 
- `KAFKA_BOOTSTRAP_SERVERS=kafka:9093` - Sử dụng `kafka:9093` cho Docker internal network
- Port `9092` được expose ra ngoài cho các client bên ngoài Docker
- Port `9093` được sử dụng cho communication giữa các container

### Bước 2: Khởi động lại hệ thống

```bash
# Dừng các container hiện tại
docker-compose down

# Xóa volumes cũ (nếu cần)
docker-compose down -v

# Khởi động lại với Kafka
docker-compose up -d

# Xem logs để kiểm tra
docker-compose logs -f kafka
docker-compose logs -f ai_server
```

### Bước 3: Kiểm tra Kafka đã hoạt động

```bash
# Kiểm tra các container
docker ps

# Kiểm tra Kafka topics
docker exec vrecom_kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Bước 4: Test hệ thống

Kafka sẽ tự động tạo topic khi có message đầu tiên. Bạn có thể test bằng cách:

```bash
# Tạo một message test
docker exec vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic interactions
# Sau đó nhập một JSON message:
{"user_id": "test_user", "item_id": "test_item", "action": "view", "timestamp": "2025-01-23T00:00:00"}
# Nhấn Ctrl+C để thoát

# Đọc messages
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interactions --from-beginning
```

---

## 💻 Cách 2: Chạy Kafka Riêng (Cho Development)

Nếu bạn muốn chạy Kafka riêng biệt và AI server ở local:

### Bước 1: Khởi động Kafka test server

```bash
cd tests/kafka-server
docker-compose up -d
```

### Bước 2: Cập nhật biến môi trường

Khi chạy AI server ở local, set biến môi trường:

```bash
# Windows (PowerShell)
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
$env:KAFKA_GROUP_ID="vrecom_ai_server_group"

# Linux/Mac
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_GROUP_ID="vrecom_ai_server_group"
```

### Bước 3: Khởi động AI server

```bash
cd backend/ai_server
poetry run python -m ai_server.main
```

---

## 🔍 Troubleshooting

### Lỗi: Kafka container không start

```bash
# Xem logs chi tiết
docker-compose logs kafka

# Kiểm tra Zookeeper
docker-compose logs zookeeper

# Thử start lại
docker-compose restart zookeeper
docker-compose restart kafka
```

### Lỗi: Connection timeout

```bash
# Kiểm tra network
docker network inspect vrecommendation_vrecom_network

# Kiểm tra xem các service có kết nối được không
docker exec vrecom_ai_server ping kafka
```

### Lỗi: Port đã được sử dụng

```bash
# Kiểm tra port 9092
netstat -ano | findstr :9092    # Windows
lsof -i :9092                   # Linux/Mac

# Thay đổi port trong .env
KAFKA_PORT=9094
```

### Lỗi: Consumer group không reset

```bash
# Reset consumer group offset
docker exec vrecom_kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group vrecom_ai_server_group --reset-offsets --to-earliest --all-topics --execute
```

---

## 🎯 Kiểm Tra Hệ Thống Hoạt Động

### 1. Kiểm tra các services

```bash
docker-compose ps
```

Tất cả services nên có status `Up`:
- vrecom_zookeeper
- vrecom_kafka
- vrecom_ai_server
- vrecom_api_server
- vrecom_redis
- vrecom_frontend
- vrecom_prometheus

### 2. Kiểm tra logs không còn lỗi

```bash
docker-compose logs -f ai_server | grep -i "kafka\|rdkafka"
```

Không nên thấy lỗi "Connection refused" nữa.

### 3. Test API tạo Data Chef từ Kafka

```bash
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

### 4. Test training model với Kafka data

```bash
# Tạo model
curl -X POST http://localhost:9999/api/v1/private/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "kafka_model",
    "algorithm": "nmf"
  }'

# Tạo task training với Kafka data chef
curl -X POST http://localhost:9999/api/v1/private/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "kafka_training_task",
    "model_id": "kafka_model",
    "data_chef_id": "kafka_interactions",
    "interval": 3600
  }'
```

---

## 📝 Lưu Ý Quan Trọng

### Về Docker Network

- **Trong Docker network**: Sử dụng service name `kafka:9093`
- **Từ host machine**: Sử dụng `localhost:9092`
- Không sử dụng `localhost` hoặc `127.0.0.1` trong Docker environment variables

### Về Data Persistence

Kafka data được lưu trong Docker volumes:
- `kafka_data`: Lưu messages và topics
- `zookeeper_data`: Lưu metadata của Kafka

Để xóa toàn bộ data và bắt đầu lại từ đầu:
```bash
docker-compose down -v
docker-compose up -d
```

### Về Performance

- Default retention: 7 ngày (168 giờ)
- Auto create topics: Enabled
- Replication factor: 1 (cho development)

Cho production, nên tăng:
- `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3`
- Add thêm Kafka brokers
- Tăng `KAFKA_LOG_RETENTION_HOURS`

---

## 🚀 Quick Start Commands

```bash
# Start toàn bộ hệ thống
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop hệ thống
docker-compose down

# Restart một service
docker-compose restart kafka
docker-compose restart ai_server

# Clean up everything
docker-compose down -v
docker system prune -a
```

---

## 📚 Tài Liệu Tham Khảo

- [Confluent Kafka Docker Guide](https://docs.confluent.io/platform/current/installation/docker/installation.html)
- [Kafka Python Client](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)

---

## 💡 Tips

1. **Development**: Sử dụng Kafka UI để monitor topics và messages:
   - Truy cập: http://localhost:8080 (nếu bạn thêm kafka-ui service)
   
2. **Production**: Cân nhắc sử dụng managed Kafka service như:
   - Confluent Cloud
   - AWS MSK
   - Azure Event Hubs

3. **Monitoring**: Theo dõi Kafka metrics qua Prometheus (đã có trong docker-compose)

---

**Cập nhật lần cuối**: 2025-01-23  
**Version**: 1.0.0