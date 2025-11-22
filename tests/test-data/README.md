# Test Data for VRecommendation System

This directory contains sample test data for training and testing recommendation models.

## Files

### interactions.csv

Sample user-item interaction data with ratings.

**Format:**
```csv
user_id,item_id,rating,timestamp
```

**Fields:**
- `user_id`: Unique user identifier
- `item_id`: Unique item identifier
- `rating`: Rating value (1.0 - 5.0)
- `timestamp`: ISO 8601 timestamp

**Statistics:**
- Total interactions: 60
- Unique users: 20
- Unique items: 10
- Rating range: 3.0 - 5.0
- Time span: 2025-11-15 10:00 - 15:00

## Usage

### With CSV Data Chef

```bash
# Create data chef from CSV file
curl -X POST http://localhost:9999/api/v1/create_data_chef_from_csv \
  -H "Content-Type: application/json" \
  -d '{
    "name": "csv_test_data",
    "path": "/app/tests/test-data/interactions.csv",
    "rename_columns": ""
  }'

# Create model
curl -X POST http://localhost:9999/api/v1/create_model \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "test_model",
    "algorithm": "svd",
    "hyperparameters": {
      "n_components": 5,
      "n_iter": 20
    }
  }'

# Train model with scheduled task
curl -X POST http://localhost:9999/api/v1/add_model_task \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "test_training",
    "model_id": "test_model",
    "interactions_data_chef_id": "csv_test_data",
    "interval": 3600
  }'
```

### Direct Training Script

```python
import pandas as pd
from ai_server.services.model_service import ModelService

# Load CSV data
df = pd.read_csv('interactions.csv')

# Initialize model service
model_service = ModelService()

# Create and train model
model_service.initialize_training(
    model_id='test_model',
    algorithm='svd',
    hyperparameters={'n_components': 5}
)

# Train with data
for _, row in df.iterrows():
    model_service.train_batch('test_model', [row.to_dict()])

# Finalize and save
model_service.finalize_training('test_model')
model_service.save_model('test_model')
```

## Data Characteristics

### User Distribution
- Each user has 3 interactions on average
- Rating distribution:
  - 5.0 stars: 40%
  - 4.5 stars: 30%
  - 4.0 stars: 15%
  - 3.5 stars: 10%
  - 3.0 stars: 5%

### Item Distribution
- Each item has 6 interactions on average
- Popular items: item001, item002, item003
- Less popular items: item007, item008, item009, item010

### Use Cases
- Cold start testing: New users/items not in dataset
- Recommendation quality evaluation
- Model comparison and benchmarking
- Performance testing with known data patterns

## Generating Additional Test Data

Use the provided scripts to generate more test data:

```bash
# Generate larger dataset
python generate_test_data.py --users 100 --items 50 --interactions 1000

# Generate data with specific patterns
python generate_test_data.py --pattern popularity-bias

# Generate data with timestamps
python generate_test_data.py --time-range 30d
```

## Data Quality

This dataset is designed for testing purposes with:
- No missing values
- No duplicate user-item pairs
- Consistent timestamp ordering
- Realistic rating distribution
- Sufficient sparsity for collaborative filtering

## Integration Tests

Run integration tests with this data:

```bash
# Test CSV data chef
python -m pytest tests/test_csv_data_chef.py

# Test model training
python -m pytest tests/test_model_training.py

# Test recommendations
python -m pytest tests/test_recommendations.py
```
