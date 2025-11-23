# Training Data Generation Guide

## 🎯 Tại Sao Cần Nhiều Dữ Liệu Training?

Recommendation models cần nhiều dữ liệu để:
- **Học patterns** - Hiểu user preferences và item relationships
- **Generalization** - Đưa ra recommendations tốt cho diverse scenarios
- **Cold start** - Xử lý users/items mới
- **Accuracy** - Tăng độ chính xác của predictions

**Minimum Recommendations:**
- Development/Testing: 1,000-5,000 interactions
- Production Training: 20,000-50,000 interactions
- High-Quality Models: 100,000+ interactions

---

## 🚀 Quick Start

### Option 1: Large-Scale Training Data Generator (RECOMMENDED)

```bash
cd tests/kafka-server

# Generate large realistic dataset
python generate_training_data.py

# Configuration prompts:
# → Users: 500
# → Items: 1000
# → Interactions: 50000
# → Output: 3 (Send to Kafka)
```

**Expected Time:** ~30 seconds for 50k interactions

### Option 2: Enhanced Producer with Synthetic Data

```bash
# Generate medium dataset
python kafka_producer.py

# Select:
# → Data source: 2 (Generate synthetic data)
# → Count: 5000
# → Mode: 1 (Batch mode - fastest)
```

**Expected Time:** ~10 seconds for 5k interactions

### Option 3: Quick Test Data

```bash
# Small dataset for quick testing
python test_kafka_connection.py
```

**Generates:** 100 interactions automatically

---

## 📊 Data Options Comparison

| Script | Users | Items | Interactions | Patterns | Use Case |
|--------|-------|-------|--------------|----------|----------|
| `test_kafka_connection.py` | 20 | 50 | 100 | Basic | Quick test |
| `kafka_producer.py` | 100 | 200 | 1K-10K | Medium | Development |
| `generate_training_data.py` | **500+** | **1000+** | **10K-100K+** | **Advanced** | **Production** |

---

## 🎨 Realistic Patterns Included

### User Behavior Patterns

**Pareto Principle (80-20 Rule):**
- 20% active users create 80% of interactions
- Mimics real-world user engagement

**User Clusters:**
- Tech Enthusiasts (15%) - Prefer electronics
- Fashion Lovers (15%) - Prefer fashion items
- Home Makers (15%) - Prefer home products
- Sports Fans (15%) - Prefer sports equipment
- Bookworms (15%) - Prefer books
- General Users (25%) - Mixed preferences

**Interaction Patterns:**
- 60% interactions with preferred items
- 30% interactions with popular items
- 10% random exploration

### Item Patterns

**Categories (5 types):**
- Electronics (20%)
- Fashion (20%)
- Home (20%)
- Sports (20%)
- Books (20%)

**Popularity Distribution:**
- Top 10% items = Popular items
- Get 30% of all interactions
- Realistic long-tail distribution

### Rating Distributions

```
Preferred Items:    4.0-5.0 ★★★★★ (High satisfaction)
Popular Items:      3.0-5.0 ★★★☆☆ (Generally positive)
Random Items:       1.0-5.0 ★☆☆☆☆ (Diverse opinions)
```

**Expected Distribution:**
- 5.0 stars: 15%
- 4.5 stars: 18%
- 4.0 stars: 21%
- 3.5 stars: 13%
- 3.0 stars: 12%
- 2.5 stars: 6%
- 2.0 stars: 5.5%
- 1.5 stars: 4.5%
- 1.0 stars: 5%

---

## 🛠️ Complete Workflow

### Step 1: Start Kafka

```bash
cd tests/kafka-server
docker-compose up -d

# Wait 5 seconds for Kafka to start
sleep 5
```

### Step 2: Generate Training Data

```bash
# Option A: Large production dataset
python generate_training_data.py
# Config: 500 users, 1000 items, 50000 interactions
# Output: Send to Kafka

# Option B: Medium development dataset
python kafka_producer.py
# Source: Generate synthetic (option 2)
# Count: 10000
# Mode: Batch (option 1)
```

### Step 3: Verify Data Received

```bash
# Consume sample to verify
python kafka_consumer_test.py
# Mode: 2 (Consume limited)
# Max messages: 50
```

**Expected Sample Output:**
```
[Message #1]
  User: user_15
  Item: item_234
  Rating: 4.5
  Timestamp: 2024-01-15T10:30:00Z

[Message #2]
  User: user_3
  Item: item_89
  Rating: 5.0
  Timestamp: 2024-01-15T11:45:00Z
```

### Step 4: Train Model

Model sẽ tự động consume data từ Kafka:

```bash
# VRecommendation AI Server sẽ:
# 1. Connect to Kafka as Consumer (with group.id)
# 2. Read all interactions
# 3. Train recommendation model
# 4. Save trained model
```

---

## 📈 Dataset Statistics Example

**After generating 50,000 interactions:**

```
======================================================================
Dataset Statistics
======================================================================
Total Users: 500
Total Items: 1000
Total Interactions: 50000
Unique Active Users: 400 (80%)
Unique Items with Interactions: 950 (95%)

Average Rating: 3.85 ⭐
Avg Interactions per User: 100
Max Interactions per User: 350 (power user!)
Min Interactions per User: 12

Rating Distribution:
  5.0:  7500 (15.00%) ★★★★★
  4.5:  9000 (18.00%) ★★★★☆
  4.0: 10500 (21.00%) ★★★★☆
  3.5:  6500 (13.00%) ★★★☆☆
  3.0:  6000 (12.00%) ★★★☆☆
  2.5:  3000 ( 6.00%) ★★☆☆☆
  2.0:  2750 ( 5.50%) ★★☆☆☆
  1.5:  2250 ( 4.50%) ★☆☆☆☆
  1.0:  2500 ( 5.00%) ★☆☆☆☆
======================================================================
```

**This gives model:**
- 400 users to learn preferences from
- 950 items to recommend
- 50,000 user-item interactions
- Diverse rating patterns (1.0-5.0)
- Realistic behavior patterns

---

## 💡 Best Practices

### 1. Data Size Recommendations

**Development:**
```bash
python generate_training_data.py
# Users: 100
# Items: 300
# Interactions: 5000
```

**Testing:**
```bash
python generate_training_data.py
# Users: 200
# Items: 500
# Interactions: 20000
```

**Production:**
```bash
python generate_training_data.py
# Users: 500-1000
# Items: 1000-5000
# Interactions: 50000-100000+
```

### 2. Progressive Training

Start small, scale up:

```bash
# Week 1: Test with small dataset
python generate_training_data.py  # 5k interactions

# Week 2: Medium dataset
python generate_training_data.py  # 20k interactions

# Week 3: Large dataset
python generate_training_data.py  # 50k interactions

# Production: Very large dataset
python generate_training_data.py  # 100k+ interactions
```

### 3. Verify Data Quality

After generation, check:

```bash
# Consume sample
python kafka_consumer_test.py

# Verify:
# ✓ User IDs diverse (user_1, user_50, user_200)
# ✓ Item IDs diverse (item_1, item_300, item_800)
# ✓ Ratings vary (1.0 to 5.0)
# ✓ Timestamps spread over time
```

### 4. Export Options

```bash
python generate_training_data.py

# Choose output:
# 1. CSV - Easy to inspect and analyze
# 2. JSON - Structured format with metadata
# 3. Kafka - Direct to training pipeline ✓ RECOMMENDED
# 4. All - Backup + training
```

---

## 🔧 Configuration Examples

### Example 1: Small Development Dataset

```bash
python generate_training_data.py
```

**Input:**
- Users: 100
- Items: 300
- Interactions: 5000
- Output: Send to Kafka

**Use Case:** Quick model testing, fast iterations

### Example 2: Medium Testing Dataset

```bash
python generate_training_data.py
```

**Input:**
- Users: 300
- Items: 600
- Interactions: 20000
- Output: All (CSV + JSON + Kafka)

**Use Case:** Model validation, performance testing

### Example 3: Large Production Dataset

```bash
python generate_training_data.py
```

**Input:**
- Users: 1000
- Items: 3000
- Interactions: 100000
- Output: Send to Kafka

**Use Case:** Production model training, high accuracy

---

## 🐛 Troubleshooting

### Issue: Not Enough Data for Model

**Symptom:** Model accuracy low, poor recommendations

**Solution:**
```bash
# Generate more interactions
python generate_training_data.py
# Increase to 50000+ interactions
```

### Issue: Data Too Uniform

**Symptom:** Model learns but doesn't generalize

**Solution:** Use `generate_training_data.py` (has diversity built-in)
- User clusters included
- Rating variance
- Temporal spread

### Issue: Generation Too Slow

**Symptom:** Takes long time to generate data

**Solution:**
```bash
# Use batch mode for Kafka sending
python generate_training_data.py
# Output: 3 (Send to Kafka) - fastest option
```

### Issue: Can't See Generated Data

**Symptom:** Not sure if data was sent

**Solution:**
```bash
# Verify with consumer
python kafka_consumer_test.py
# Mode: 2 (limited)
# Count: 50
```

---

## 📋 Checklist for Training

Before training model, verify:

- [ ] Kafka is running (`docker ps | grep kafka`)
- [ ] Generated sufficient data (20k+ for production)
- [ ] Data has diversity (checked with consumer)
- [ ] Rating distribution looks realistic
- [ ] Temporal spread is adequate
- [ ] User/item coverage is good

---

## 🎓 Understanding the Output

### CSV Format

```csv
user_id,item_id,rating,timestamp
user_1,item_45,5.0,2024-01-15T10:30:00Z
user_2,item_123,4.5,2024-01-15T11:45:00Z
user_1,item_89,4.0,2024-01-16T09:15:00Z
```

### JSON Format

```json
{
  "metadata": {
    "generated_at": "2024-01-15T12:00:00Z",
    "num_users": 500,
    "num_items": 1000,
    "num_interactions": 50000
  },
  "interactions": [
    {
      "user_id": "user_1",
      "item_id": "item_45",
      "rating": 5.0,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "statistics": { ... }
}
```

### Kafka Format

```json
{
  "user_id": "user_1",
  "item_id": "item_45",
  "rating": 5.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🚀 Quick Commands Reference

```bash
# Generate 50k production dataset
python generate_training_data.py
# → 500, 1000, 50000, Send to Kafka

# Generate 10k development dataset
python kafka_producer.py
# → Synthetic, 10000, Batch

# Quick test (100 interactions)
python test_kafka_connection.py

# Verify data
python kafka_consumer_test.py
# → Limited, 50

# Check Kafka
docker ps | grep kafka
docker logs test_kafka
```

---

## 📞 Need Help?

**Quick Reference:** `QUICK_REFERENCE.md`
**Full Docs:** `README.md`
**Producer/Consumer:** `KAFKA_PRODUCER_VS_CONSUMER.md`

---

**Last Updated:** 2024  
**Version:** 1.0  
**Status:** ✅ Production Ready

**Recommended for Model Training:** 50,000+ interactions with realistic patterns