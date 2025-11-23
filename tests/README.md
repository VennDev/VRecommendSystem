# Tests Directory

This directory contains test resources and testing utilities for the VRecommendation system.

## Contents

### demo-website/

A demo e-commerce website for testing the recommendation system in action.

**Features:**
- User authentication and session management
- Product catalog browsing
- User interaction tracking (views, likes)
- Real-time recommendations from the AI server
- Training data API endpoint

**Usage:**
```bash
cd demo-website
npm install
npm start
```

Access at: http://localhost:3500

See `demo-website/README.md` for detailed documentation.

### kafka-server/

A standalone Kafka server setup for testing message queue data sources.

**Features:**
- Apache Kafka broker
- Zookeeper coordination service
- Kafka UI for management
- **Producer test script** (`kafka_producer.py`) - Gửi messages vào Kafka
- **Consumer test script** (`kafka_consumer_test.py`) - Nhận messages từ Kafka với group.id
- **Automated test suite** (`test_kafka_connection.py`) - Verify toàn bộ kết nối
- **Test runner scripts** (`run_tests.cmd`, `run_tests.sh`) - Interactive testing menu
- Isolated from main project

**Quick Start:**
```bash
cd kafka-server

# Option 1: Automated test (Recommended)
docker-compose up -d
python test_kafka_connection.py

# Option 2: Interactive menu
run_tests.cmd  # Windows
./run_tests.sh # Linux/Mac
```

**Key Concepts:**
- **Producer** (`kafka_producer.py`) - Gửi messages, KHÔNG CẦN `group.id`
- **Consumer** (`kafka_consumer_test.py`) - Nhận messages, BẮT BUỘC phải có `group.id`

Access Kafka UI at: http://localhost:8080

See `kafka-server/README.md` for detailed documentation.
See `kafka-server/KAFKA_PRODUCER_VS_CONSUMER.md` for Producer vs Consumer guide.

## Testing Workflow

### 1. Integration Testing with Demo Website

The demo website provides a complete testing environment:

```bash
# Start VRecommendation services
cd ../..
docker-compose up -d

# Start demo website
cd tests/demo-website
npm start

# Generate test data by interacting with the website
open http://localhost:3500
```

### 2. Message Queue Testing with Kafka

Test Kafka data source integration:

```bash
# Start Kafka server
cd tests/kafka-server
docker-compose up -d

# Option A: Run automated test suite (Recommended)
python test_kafka_connection.py
# This will verify: connection, producer, consumer, and group.id requirement

# Option B: Manual Producer-Consumer test
# Terminal 1: Start Consumer
python kafka_consumer_test.py
# Select mode 3 (continuous)

# Terminal 2: Start Producer
python kafka_producer.py
# Select mode 1 (batch)

# Option C: Use interactive test runner
run_tests.cmd  # Windows
./run_tests.sh # Linux/Mac
```

**Important Notes:**
- **Producer** does NOT require `group.id` (only sends messages)
- **Consumer** REQUIRES `group.id` (needs to track offset)
- VRecommendation AI Server acts as a Consumer → needs `group.id`

### 3. API Testing

Test API endpoints using the demo website as data source:

```bash
# Create Data Chef pointing to demo website
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_api \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo_data",
    "url": "http://localhost:3500/api/training/interactions",
    "rename_columns": ""
  }'

# Train model with demo data
curl -X POST http://localhost:9999/api/v1/add_model_task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "demo_training",
    "model_id": "demo_model",
    "interactions_data_chef_id": "demo_data",
    "interval": 3600
  }'
```

## Test Data

### Sample Interaction Data Format

```json
{
  "user_id": "user123",
  "item_id": "item456",
  "rating": 5.0,
  "timestamp": "2025-11-15T10:30:00Z"
}
```

### Generating Test Data

Use the demo website to generate realistic test data:
1. Create multiple user accounts
2. Browse and interact with products
3. Like/unlike products
4. View product details

The interactions are automatically tracked and available via:
```
http://localhost:3500/api/training/interactions
```

## Running Tests

### System-wide Tests

From project root:
```bash
# Windows
test-system.cmd

# Linux/Mac
make test
```

### Component Tests

```bash
# API Server tests
cd backend/api_server
go test ./...

# AI Server tests
cd backend/ai_server
poetry run pytest

# Frontend tests
cd frontend/project
npm test
```

## Test Environments

### Development Environment

- Demo website on port 3500
- Kafka test server on ports 9092 (broker), 8080 (UI)
- Main services on standard ports (2030, 9999, 5173)

### Isolated Testing

Each test component runs independently:
- Demo website: Standalone Node.js server
- Kafka server: Separate Docker Compose network
- No dependencies on main project services

## Troubleshooting Tests

### Demo Website Issues

```bash
# Check if port 3500 is available
netstat -ano | findstr :3500

# View demo website logs
cd tests/demo-website
npm start  # Check console output
```

### Kafka Issues

```bash
# Check Kafka containers
docker ps | grep test_kafka

# View Kafka logs
docker logs test_kafka

# Run automated diagnostics
cd tests/kafka-server
python test_kafka_connection.py

# Test Producer (no group.id needed)
python kafka_producer.py

# Test Consumer (group.id required)
python kafka_consumer_test.py

# Access Kafka UI
open http://localhost:8080
```

**Common Kafka Errors:**
- `group.id not configured` → Consumer missing group.id, add it to config
- `Connection refused` → Kafka not running, run `docker-compose up -d`
- Port 9092 in use → Stop other Kafka instances

### Data Issues

```bash
# Verify demo data
curl http://localhost:3500/api/training/interactions

# Check data format
curl http://localhost:3500/api/training/interactions | jq .
```

## Best Practices

1. **Isolate Test Data**: Use separate databases/files for testing
2. **Clean Up**: Reset test data between test runs
3. **Mock External Services**: Use demo website instead of production APIs
4. **Version Test Data**: Keep test datasets version controlled
5. **Document Tests**: Add comments explaining test scenarios

## Adding New Tests

### Adding a Test Service

1. Create new directory under `tests/`
2. Add README.md with documentation
3. Include docker-compose.yml if using Docker
4. Add .gitignore for generated files
5. Update this README with new test info

### Example Test Service Structure

```
tests/new-service/
├── README.md              # Service documentation
├── docker-compose.yml     # Docker configuration
├── .gitignore            # Ignore patterns
├── start.sh              # Startup script
└── data/                 # Test data
    └── .gitkeep
```

## Recent Updates

### Kafka Test Suite (2024)

**New features:**
- ✅ Consumer test script with proper `group.id` configuration
- ✅ Automated test suite for complete verification
- ✅ Interactive test runner menus (Windows & Linux/Mac)
- ✅ Comprehensive documentation on Producer vs Consumer

**Quick test:**
```bash
cd tests/kafka-server
python test_kafka_connection.py
```

See `kafka-server/SUMMARY.md` for quick overview or `kafka-server/CHANGELOG.md` for details.

## Resources

- Main documentation: `../README.md`
- Demo website docs: `demo-website/README.md`
- Kafka server docs: `kafka-server/README.md`
- Kafka quick reference: `kafka-server/QUICK_REFERENCE.md`
- Producer vs Consumer guide: `kafka-server/KAFKA_PRODUCER_VS_CONSUMER.md`
- API documentation: http://localhost:9999/docs
