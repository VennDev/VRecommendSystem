# Scripts Documentation

## Overview

This directory contains utility scripts for training and managing recommendation models with actual user interaction data.

## 🔥 Cold Start Problem - Giải Thích

### Vấn Đề

Khi bạn gặp lỗi **API `/recommend` không trả về gợi ý** (predictions rỗng), đây thường là **Cold Start Problem**:

```json
{
  "model_id": "my_model",
  "user_id": "1763038682578",
  "predictions": {},
  "status": "completed"
}
```

**Nguyên nhân:**
- Model được train với user ID cũ (ví dụ: `user1`, `user2`)
- Demo website tạo user ID mới (ví dụ: `1763038682578`)
- SVD model không tìm thấy user trong `user_id_mapping` → trả về rỗng

**Code gây lỗi** (`svd_model.py`):
```python
for user_id in user_ids:
    if user_id not in self.user_id_mapping:
        continue  # ❌ Bỏ qua user không có trong training data
```

### Giải Pháp

✅ **Train lại model với dữ liệu thực từ demo website**

## 📋 Scripts Available

### 1. `train_demo_model.py`

**Mô tả:** Script chính để train model với dữ liệu từ demo website.

**Chức năng:**
- Đọc interactions từ `tests/demo-website/data/user_actions.json`
- Convert sang format training (user_id, item_id, rating)
- Train model SVD với hyperparameters tối ưu
- Tự động tính `n_components` phù hợp với dataset
- Save model và test recommendations

**Cách sử dụng:**

```bash
# Cách 1: Chạy trong Docker container (Khuyến nghị)
docker cp scripts/train_demo_model.py vrecom_ai_server:/app/
docker cp tests/demo-website/data/user_actions.json vrecom_ai_server:/app/
docker exec vrecom_ai_server python3 /app/train_demo_model.py

# Cách 2: Nếu có Python environment local
python scripts/train_demo_model.py
```

**Output mong đợi:**

```
============================================================
🎯 Training Demo Model
============================================================

📊 Training data summary:
   Total interactions: 16
   Unique users: 2
   Unique items: 4

🔧 Configuring model 'demo_model'...
   Items in dataset: 4
   Using n_components: 3

✨ Model trained successfully!

📈 Training Metrics:
   Training time: 0.008s
   Users: 2.0
   Items: 4.0
   Interactions: 7.0
   Sparsity: 12.50%
   Explained variance: 100.00%

🔮 Testing recommendations for user 1763038682578...
✅ Got 4 recommendations:
   → Item 5 (score: 5.000)
   → Item 4 (score: 1.000)
   → Item 2 (score: 1.000)
   → Item 1 (score: 1.000)

============================================================
✅ Training completed successfully!
   Model ID: demo_model
============================================================
```

**Model được tạo:**
- `models/demo_model.pkl` - Model weights
- `models/demo_model_config.json` - Configuration
- `models/demo_model_metadata.json` - Metadata & metrics

---

### 2. `train_with_demo_data.py`

**Mô tả:** Script để train model qua REST API (cần authentication).

**Chức năng:**
- Fetch data từ demo website API hoặc local file
- Gọi API endpoints để train model:
  - `POST /api/v1/initialize_training`
  - `POST /api/v1/train_batch`
  - `POST /api/v1/finalize_training`
- Test recommendations sau khi train

**Cách sử dụng:**

```bash
# Đảm bảo demo website đang chạy
cd tests/demo-website
npm start

# Chạy script (từ root directory)
python scripts/train_with_demo_data.py
```

**Lưu ý:** Script này cần authentication token nếu API endpoints không public.

---

## 🚀 Quick Start Guide

### Bước 1: Tạo Dữ Liệu Test

1. **Khởi động hệ thống:**
   ```bash
   start.cmd
   ```

2. **Khởi động demo website:**
   ```bash
   cd tests/demo-website
   npm install
   npm start
   ```

3. **Tạo interactions:**
   - Mở browser: `http://localhost:3500`
   - Login với username/password
   - Like/view một số products
   - Data sẽ được lưu vào `tests/demo-website/data/user_actions.json`

### Bước 2: Train Model

```bash
# Copy script và data vào container
docker cp scripts/train_demo_model.py vrecom_ai_server:/app/
docker cp tests/demo-website/data/user_actions.json vrecom_ai_server:/app/

# Train model
docker exec vrecom_ai_server python3 /app/train_demo_model.py
```

### Bước 3: Test Recommendations

```bash
# Test qua AI Server trực tiếp
curl "http://localhost:9999/api/v1/recommend/<USER_ID>/demo_model/5"

# Test qua API Server (có caching)
curl "http://localhost:2030/api/v1/recommend?user_id=<USER_ID>&model_id=demo_model&n=5"
```

**Thay `<USER_ID>`** bằng user ID thực từ demo website (ví dụ: `1763038682578`).

---

## 📊 Model Configuration

### Hyperparameters

Script tự động tính toán `n_components` dựa trên dataset:

```python
n_items = len(set(item_ids))
n_components = min(n_items - 1, 10)  # Must be < n_items
```

**Default hyperparameters:**
```json
{
  "n_components": 3,        // Tự động điều chỉnh
  "algorithm": "randomized",
  "n_iter": 10,
  "random_state": 42,
  "tol": 0.0
}
```

### Data Format

**Input format** (`user_actions.json`):
```json
[
  {
    "userId": "1763038682578",
    "productId": 2,
    "action": "like",
    "timestamp": "2025-11-15T00:59:47.979Z"
  },
  {
    "userId": "1763038682578",
    "productId": 1,
    "action": "view",
    "timestamp": "2025-11-15T00:59:49.269Z"
  }
]
```

**Training format** (after conversion):
```json
[
  {
    "user_id": "1763038682578",
    "item_id": "2",
    "rating": 5.0,
    "timestamp": "2025-11-15T00:59:47.979Z"
  }
]
```

**Rating mapping:**
- `like` action → `rating: 5.0`
- `view` action → `rating: 1.0`

---

## 🐛 Troubleshooting

### Lỗi: "No recommendations returned"

**Nguyên nhân:** User ID không có trong training data.

**Giải pháp:**
1. Kiểm tra user ID có trong `user_actions.json`
2. Train lại model với data mới
3. Đảm bảo dùng đúng `model_id` (demo_model thay vì my_model)

### Lỗi: "n_components must be <= n_features"

**Nguyên nhân:** Dataset quá nhỏ (ít items).

**Giải pháp:** Script tự động fix bằng cách tính:
```python
n_components = min(n_items - 1, 10)
```

Nếu vẫn lỗi, thêm nhiều products vào demo website.

### Lỗi: "Model not found" hoặc "config.json not found"

**Nguyên nhân:** Model chưa được save.

**Giải pháp:** Script đã bao gồm `save_model()`. Nếu vẫn lỗi:
```bash
# Kiểm tra model files
docker exec vrecom_ai_server ls -la /app/models/

# Phải có:
# demo_model.pkl
# demo_model_config.json
# demo_model_metadata.json
```

### Lỗi: "Authentication required"

**Nguyên nhân:** Endpoint cần authentication.

**Giải pháp:**
- Dùng `train_demo_model.py` (chạy trong container, bypass auth)
- Hoặc thêm `/api/v1/initialize_training` vào `public_paths` trong `auth_middleware.py`

---

## 📈 Performance Tips

### 1. Dataset Size

**Minimum requirements:**
- ≥ 2 users
- ≥ 2 items
- ≥ 4 interactions

**Recommended:**
- 10+ users
- 20+ items
- 100+ interactions

### 2. Hyperparameters Tuning

**Small dataset** (< 10 items):
```python
n_components = 2-5
n_iter = 5-10
```

**Medium dataset** (10-100 items):
```python
n_components = 5-20
n_iter = 10-20
```

**Large dataset** (100+ items):
```python
n_components = 20-50
n_iter = 20-50
```

### 3. Rating Strategy

**Current mapping:**
- like = 5.0 (positive signal)
- view = 1.0 (neutral signal)

**Alternative strategies:**
- view = 1.0, like = 5.0, dislike = 0.0
- Implicit feedback: tất cả = 1.0
- Weighted by frequency: view nhiều = rating cao hơn

---

## 🔄 Re-training Workflow

### Khi nào cần retrain?

1. **Có users mới** → Cold start problem
2. **Có items mới** → Model không biết items mới
3. **Behavior thay đổi** → Recommendations không còn relevant
4. **Dataset lớn hơn** → Model có thể học tốt hơn

### Automated Retraining

**Option 1: Cron job**
```bash
# Trong container, tạo cron job
0 */6 * * * python3 /app/train_demo_model.py >> /app/logs/training.log 2>&1
```

**Option 2: Webhook từ demo website**
```javascript
// Sau khi user interact
if (totalInteractions % 100 === 0) {
  await axios.post('http://ai_server:9999/api/v1/retrain', {
    model_id: 'demo_model'
  });
}
```

**Option 3: Manual**
```bash
# Chạy script bất cứ khi nào cần
docker exec vrecom_ai_server python3 /app/train_demo_model.py
```

---

## 🎯 Next Steps

### 1. Handle Cold Start Better

**Hybrid approach:**
- User mới → Popular items (most liked)
- User có history → SVD recommendations
- Blend cả hai strategies

### 2. Content-Based Fallback

Khi user không có trong model:
- Dùng item features (category, tags)
- Content-based filtering
- Return popular items in same category

### 3. Online Learning

- Incremental training với data mới
- Update model weights without full retrain
- Dùng `train_batch()` để add new interactions

### 4. A/B Testing

- Train multiple models (demo_model_v1, demo_model_v2)
- Compare metrics (CTR, conversion)
- Deploy best performing model

---

## 📚 Additional Resources

**Files to check:**
- `backend/ai_server/src/ai_server/models/svd_model.py` - SVD implementation
- `backend/ai_server/src/ai_server/services/model_service.py` - Model service
- `tests/demo-website/server.js` - Demo website API

**Endpoints:**
- `GET /api/v1/recommend/{user_id}/{model_id}/{n}` - Get recommendations
- `GET /api/v1/list_models` - List all trained models
- `POST /api/v1/initialize_training` - Initialize training (private)
- `POST /api/v1/train_batch` - Train batch (private)
- `POST /api/v1/finalize_training` - Finalize training (private)

**Docker commands:**
```bash
# View logs
docker logs vrecom_ai_server -f

# Execute commands in container
docker exec vrecom_ai_server <command>

# Copy files
docker cp <local_path> vrecom_ai_server:<container_path>

# Restart services
docker-compose restart ai_server
```

---

## 💡 Summary

**Vấn đề gốc:** API `/recommend` không trả về gợi ý vì user_id mới không có trong training data.

**Giải pháp:** Dùng `train_demo_model.py` để train model với data thực từ demo website.

**Kết quả:** Model `demo_model` có thể gợi ý cho users thực từ demo website.

**Next time:** Mỗi khi có users/interactions mới, chạy lại training script để update model.

---

**Happy Recommending! 🎉**