# Changelog - Kafka Integration

## [1.0.0] - 2025-01-23

### 🎯 Tóm Tắt

Tích hợp hoàn chỉnh Apache Kafka vào hệ thống VRecommendation để hỗ trợ xử lý dữ liệu real-time từ message queue.

### ✨ Thêm Mới

#### Services
- **Zookeeper Service** (`vrecom_zookeeper`)
  - Image: `confluentinc/cp-zookeeper:7.5.0`
  - Port: 2181
  - Volumes: `zookeeper_data`, `zookeeper_logs`

- **Kafka Service** (`vrecom_kafka`)
  - Image: `confluentinc/cp-kafka:7.5.0`
  - Ports: 9092 (external), 9093 (internal)
  - Auto create topics enabled
  - Retention: 7 days (168 hours)
  - Volume: `kafka_data`

- **Kafka UI Service** (`vrecom_kafka_ui`) - Optional
  - Image: `provectuslabs/kafka-ui:latest`
  - Port: 8080
  - Web interface: http://localhost:8080

#### Environment Variables
```env
KAFKA_PORT=9092
KAFKA_UI_PORT=8080
KAFKA_BOOTSTRAP_SERVERS=kafka:9093
KAFKA_GROUP_ID=vrecom_ai_server_group
```

#### Scripts
- `kafka-start.cmd` - Interactive Kafka management script
  - Start/Stop Kafka
  - View logs
  - List/Create topics
  - Clean data
  - Status checking

#### Documentation
- `KAFKA_FIX_GUIDE.md` - Hướng dẫn chi tiết sửa lỗi và cấu hình
- `KAFKA_QUICK_FIX.md` - Hướng dẫn nhanh 3 bước
- `CHANGELOG_KAFKA.md` - File này

### 🔧 Thay Đổi

#### File: `docker-compose.yml`
- Thêm Zookeeper service với persistent storage
- Thêm Kafka service với cấu hình production-ready
- Thêm Kafka UI service cho monitoring
- Cập nhật AI Server environment variables với Kafka config
- Thêm 3 volumes mới: `zookeeper_data`, `zookeeper_logs`, `kafka_data`

#### File: `example-env`
- Thêm section "Kafka Configuration"
- Thêm 4 biến môi trường mới cho Kafka

#### File: `backend/ai_server/src/ai_server/services/data_chef_service.py`
- **Import mới**: Thêm `os` và `Optional` từ typing
- **Function `_cook_messaging_queue`**:
  - Thêm fallback đến environment variables cho `brokers`, `topic`, `group_id`
  - Default `brokers`: `kafka:9093` (Docker) hoặc từ `KAFKA_BOOTSTRAP_SERVERS`
  - Default `topic`: `interactions` hoặc từ `KAFKA_DEFAULT_TOPIC`
  - Default `group_id`: `data_chef_group` hoặc từ `KAFKA_GROUP_ID`
  - Cải thiện error handling
- **Code formatting**: Cải thiện formatting theo PEP8 standards

### 🐛 Sửa Lỗi

#### Lỗi: Connection Refused to localhost:9092
**Triệu chứng:**
```
%3|1763859450.370|FAIL|rdkafka#consumer-7| 
[thrd:localhost:9092/bootstrap]: localhost:9092/bootstrap: 
Connect to ipv4#127.0.0.1:9092 failed: Connection refused
```

**Nguyên nhân:**
1. Kafka service không tồn tại trong docker-compose
2. AI Server cố kết nối đến localhost:9092 trong Docker network
3. Không có environment variable cho Kafka configuration

**Giải pháp:**
1. ✅ Thêm Zookeeper và Kafka services vào docker-compose
2. ✅ Cấu hình KAFKA_BOOTSTRAP_SERVERS=kafka:9093 cho Docker network
3. ✅ Cập nhật code để sử dụng environment variables
4. ✅ Expose port 9092 cho external access

### 📊 Kiến Trúc Mới

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │   AI Server     │
│   (React+Vite)  │◄──►│   (Go/Fiber)    │◄──►│   (Python)      │
│   Port: 5173    │    │   Port: 2030    │    │   Port: 9999    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │     Redis       │    │   Prometheus    │
                    │   (Cache/DB)    │    │  (Monitoring)   │
                    │   Port: 6379    │    │   Port: 9090    │
                    └─────────────────┘    └─────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Zookeeper     │    │     Kafka       │
                    │   Port: 2181    │◄──►│   Port: 9092/3  │
                    └─────────────────┘    └─────────────────┘
                                                    │
                                          ┌─────────────────┐
                                          │   Kafka UI      │
                                          │   Port: 8080    │
                                          └─────────────────┘
```

### 🔀 Breaking Changes

**Không có breaking changes** - Tất cả thay đổi đều backward compatible.

Hệ thống vẫn hoạt động bình thường nếu:
- Kafka không được sử dụng
- Không có Data Chef nào được cấu hình với message queue

### 📝 Migration Guide

#### Nếu Bạn Đang Chạy Hệ Thống Hiện Tại

1. **Stop hệ thống:**
   ```bash
   docker-compose down
   ```

2. **Cập nhật file `.env`:**
   ```bash
   # Sao chép từ example-env hoặc thêm thủ công:
   KAFKA_PORT=9092
   KAFKA_UI_PORT=8080
   KAFKA_BOOTSTRAP_SERVERS=kafka:9093
   KAFKA_GROUP_ID=vrecom_ai_server_group
   ```

3. **Pull images mới:**
   ```bash
   docker-compose pull
   ```

4. **Start lại hệ thống:**
   ```bash
   docker-compose up -d
   ```

5. **Verify:**
   ```bash
   docker-compose ps
   docker-compose logs kafka
   ```

#### Nếu Bạn Có Kafka Riêng (External)

Thêm vào `.env`:
```env
KAFKA_BOOTSTRAP_SERVERS=your-kafka-host:9092
KAFKA_GROUP_ID=your-group-id
```

Và comment out Kafka services trong `docker-compose.yml` nếu không cần.

### 🧪 Testing

#### Test Kafka Connection
```bash
docker exec vrecom_kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

#### Test Producer
```bash
docker exec vrecom_kafka kafka-console-producer --bootstrap-server localhost:9092 --topic interactions
# Nhập: {"user_id": "user1", "item_id": "item1", "action": "view"}
```

#### Test Consumer
```bash
docker exec vrecom_kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic interactions --from-beginning
```

#### Test với AI Server
```bash
# Tạo Data Chef từ Kafka
curl -X POST http://localhost:9999/api/v1/private/data-chef/message-queue \
  -H "Content-Type: application/json" \
  -d '{
    "data_chef_id": "kafka_test",
    "brokers": "kafka:9093",
    "topic": "interactions",
    "group_id": "test_group",
    "rename_columns": "user_id:user_id,item_id:item_id"
  }'
```

### 📈 Performance Impact

- **Storage**: +~500MB cho Kafka và Zookeeper images
- **Memory**: +~512MB khi Kafka đang chạy
- **Startup Time**: +~10-15 giây cho Kafka initialization
- **Network**: Minimal overhead (internal Docker network)

### 🔒 Security Notes

- Kafka chưa có authentication (phù hợp cho development)
- Port 9092 exposed cho external access
- Port 9093 chỉ dùng cho internal Docker network

**Khuyến nghị cho Production:**
- Enable SASL authentication
- Use SSL/TLS encryption
- Restrict port exposure
- Increase replication factor
- Add more Kafka brokers

### 📚 Dependencies

#### New Docker Images
- `confluentinc/cp-zookeeper:7.5.0`
- `confluentinc/cp-kafka:7.5.0`
- `provectuslabs/kafka-ui:latest`

#### Python Packages (đã có sẵn)
- `confluent-kafka-python` - Kafka client library

### 🎯 Next Steps

#### Recommended Enhancements
1. [ ] Add Kafka Schema Registry
2. [ ] Implement Kafka Connect for easier data integration
3. [ ] Add Kafka monitoring with JMX exporters
4. [ ] Implement SASL/SSL for production
5. [ ] Add automated topic creation scripts
6. [ ] Implement dead letter queue pattern
7. [ ] Add Kafka Streams for real-time processing

#### Production Checklist
- [ ] Configure authentication (SASL/SCRAM)
- [ ] Enable SSL/TLS encryption
- [ ] Set up multiple Kafka brokers (cluster)
- [ ] Configure proper retention policies
- [ ] Set up backup and disaster recovery
- [ ] Configure monitoring and alerting
- [ ] Document topic naming conventions
- [ ] Set up access control lists (ACLs)

### 👥 Contributors

- VennDev - Initial Kafka integration and documentation

### 📄 License

Same as project license.

---

**Full Documentation**: See `KAFKA_FIX_GUIDE.md` for detailed setup instructions.  
**Quick Start**: See `KAFKA_QUICK_FIX.md` for 3-step setup.  
**Issues**: Report at project issue tracker.