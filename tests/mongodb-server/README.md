# MongoDB Test Server

A standalone MongoDB server setup for testing NoSQL data sources with the VRecommendation system.

## Overview

This setup includes:
- MongoDB 7.0 database server
- Mongo Express web interface for database management
- Isolated test environment separate from the main project

## Prerequisites

- Docker
- Docker Compose
- Python 3.7+ (for insert script)

## Getting Started

### Start the MongoDB Server

```bash
docker-compose up -d
```

### Stop the MongoDB Server

```bash
docker-compose down
```

### Stop and Remove All Data

```bash
docker-compose down -v
```

## Access Points

- **MongoDB Server**: `localhost:27017`
- **Mongo Express UI**: `http://localhost:8081`
  - Username: `admin`
  - Password: `admin`

## Database Configuration

- **Admin Username**: `admin`
- **Admin Password**: `password123`
- **Test Database**: `vrecom_test`
- **Test Collection**: `interactions`

## Inserting Test Data

A Python script is provided to populate MongoDB with test interaction data.

### Setup

```bash
# Install required packages
pip install -r requirements.txt
```

### Usage

```bash
# Run the insert script
python mongo_insert.py
```

The script offers six operations:
1. **Insert data (batch mode)**: Insert all records at once (fast)
2. **Insert data (one by one)**: Insert records individually (slow but shows progress)
3. **Clear collection and insert**: Remove existing data and insert fresh
4. **Show collection stats**: Display database statistics
5. **Run example queries**: Execute sample queries to test data
6. **Clear collection only**: Remove all documents

### Example Output

```
VRecommendation MongoDB Inserter
Loaded 60 interactions from CSV
Connected to MongoDB successfully
Inserting 60 documents into MongoDB...

SUCCESS: Inserted 60 documents

COLLECTION STATISTICS
Total documents: 60
Unique users: 20
Unique items: 10
Average rating: 4.23
Rating range: 3.0 - 5.0
```

## Using Mongo Express

Access the web interface at http://localhost:8081

Features:
- Browse collections and documents
- Run queries with visual query builder
- Import/export data
- View collection statistics
- Manage indexes

## Integration with VRecommendation

### Create NoSQL Data Chef

```bash
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_nosql \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mongo_test_data",
    "database": "vrecom_test",
    "collection": "interactions",
    "rename_columns": ""
  }'
```

### Configure MongoDB Connection

Ensure AI server has MongoDB connection configured in `.env`:

```env
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password123
```

### Train Model with MongoDB Data

```bash
curl -X POST http://localhost:9999/api/v1/add_model_task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "mongo_training",
    "model_id": "mongo_model",
    "interactions_data_chef_id": "mongo_test_data",
    "interval": 3600
  }'
```

## Example Queries

### Using MongoDB Shell

```bash
# Connect to MongoDB
docker exec -it test_mongodb mongosh -u admin -p password123

# Switch to test database
use vrecom_test

# Find all interactions for a user
db.interactions.find({user_id: "user001"})

# Find high-rated items
db.interactions.find({rating: {$gte: 4.5}})

# Count interactions per user
db.interactions.aggregate([
  {$group: {_id: "$user_id", count: {$sum: 1}}},
  {$sort: {count: -1}}
])

# Get average rating by item
db.interactions.aggregate([
  {$group: {_id: "$item_id", avg_rating: {$avg: "$rating"}}},
  {$sort: {avg_rating: -1}}
])
```

### Using Python (PyMongo)

```python
from pymongo import MongoClient

client = MongoClient('mongodb://admin:password123@localhost:27017/')
db = client['vrecom_test']
collection = db['interactions']

# Find user interactions
user_interactions = list(collection.find({'user_id': 'user001'}))

# Find items with high ratings
high_rated = list(collection.find({'rating': {'$gte': 4.5}}))

# Count interactions per user
pipeline = [
    {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
results = list(collection.aggregate(pipeline))
```

## Data Schema

The interactions collection uses the following schema:

```json
{
  "_id": ObjectId("..."),
  "user_id": "user001",
  "item_id": "item001",
  "rating": 5.0,
  "timestamp": "2025-11-15T10:00:00Z",
  "created_at": ISODate("2025-11-15T10:30:00.000Z")
}
```

**Indexes:**
- `user_id` (ascending)
- `item_id` (ascending)
- `timestamp` (ascending)
- `user_id + item_id` (unique compound index)

## Troubleshooting

### Connection Issues

If you cannot connect to MongoDB:
- Ensure port 27017 is not being used by another service
- Check that Docker containers are running: `docker ps`
- Verify credentials are correct
- Check Docker logs: `docker logs test_mongodb`

### Authentication Errors

If you get authentication errors:
```bash
# Verify credentials
docker exec -it test_mongodb mongosh -u admin -p password123 --authenticationDatabase admin
```

### Data Not Showing

If data is not visible:
- Verify you're connected to the correct database: `vrecom_test`
- Check if collection exists: `show collections`
- Verify documents exist: `db.interactions.count()`

### Clean Reset

To completely reset MongoDB state:
```bash
docker-compose down -v
docker-compose up -d
# Wait for initialization
python mongo_insert.py
```

## Performance Tips

### Batch Operations

Use bulk operations for better performance:
```python
from pymongo import InsertMany

collection.insert_many(documents, ordered=False)
```

### Indexes

Ensure proper indexes for query performance:
```javascript
db.interactions.createIndex({user_id: 1})
db.interactions.createIndex({item_id: 1})
db.interactions.createIndex({timestamp: 1})
```

### Connection Pooling

Configure connection pool size:
```python
client = MongoClient(
    'mongodb://admin:password123@localhost:27017/',
    maxPoolSize=50
)
```

## Notes

- This setup uses a standalone MongoDB instance suitable for testing only
- Data persists in Docker volumes. Use `docker-compose down -v` to remove all data
- Mongo Express provides a web interface for easier database management
- This is completely isolated from the main VRecom project
- The insert script reads data from `../test-data/interactions.csv`
- Default authentication is configured for testing purposes only
