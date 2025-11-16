# Testing Recommendations Display

## 🎯 Overview

This document explains how to test the recommendations display functionality in the demo website.

## 🔍 Problem Description

The demo website was not displaying recommendations even when the API returned valid data. This was because:

1. **API Response Format Mismatch**: The AI server returns predictions in this format:
   ```json
   {
     "predictions": {
       "1763038682578": [
         {"item_id": "5", "score": 5}
       ]
     }
   }
   ```

2. **Frontend Expected Format**: The frontend was looking for:
   ```json
   {
     "recommendations": [
       {"item_id": "5", "score": 5}
     ]
   }
   ```

## ✅ Solution

### Backend Changes (server.js)

Modified `/api/recommendations` endpoint to transform the API response:

```javascript
// Extract recommendations from predictions object
if (apiData.predictions && apiData.predictions[req.session.user.id]) {
    recommendations = apiData.predictions[req.session.user.id].map((item, index) => ({
        item_id: item.item_id,
        score: item.score,
        rank: item.rank || index + 1,
    }));
}

// Return transformed data with both formats for compatibility
res.json({
    ...apiData,
    recommendations: recommendations,
    count: recommendations.length,
});
```

### Frontend Changes (dashboard.ejs)

Improved `loadRecommendations()` function to:
1. Handle both `recommendations` and `predictions` formats
2. Fetch product details and display full information
3. Show AI scores and rankings
4. Better error handling and logging

## 🧪 Testing Methods

### Method 1: Use Test HTML Page

1. Open `test-recommendations.html` in browser:
   ```bash
   # Copy to a web-accessible location or open directly
   start tests/demo-website/test-recommendations.html
   ```

2. Test different endpoints:
   - **AI Server Direct**: Tests `http://localhost:9999/api/v1/recommend/{user_id}/{model_id}/{n}`
   - **API Server**: Tests `http://localhost:2030/api/v1/recommend`
   - **Demo Website**: Tests `http://localhost:3500/api/recommendations`

3. View results:
   - Raw API response (JSON)
   - Parsed data (extracted fields)
   - Visual recommendations display

### Method 2: Test via Browser Console

1. Login to demo website: `http://localhost:3500`
2. Open browser DevTools (F12)
3. Run in console:

```javascript
// Test recommendations API
fetch('/api/recommendations?model_id=model_test&n=5')
  .then(res => res.json())
  .then(data => {
    console.log('API Response:', data);
    console.log('Recommendations:', data.recommendations);
    console.log('Count:', data.recommendations?.length || 0);
  });
```

### Method 3: Test with cURL

```bash
# Test AI Server Direct
curl "http://localhost:9999/api/v1/recommend/1763038682578/model_test/5"

# Test API Server
curl "http://localhost:2030/api/v1/recommend?user_id=1763038682578&model_id=model_test&n=5"

# Test Demo Website (requires authentication)
curl "http://localhost:3500/api/recommendations?model_id=model_test&n=5" \
  -H "Cookie: connect.sid=YOUR_SESSION_ID"
```

## 📊 Expected Results

### Successful Response

```json
{
  "datetime": "2025-11-15T17:05:31.871730",
  "model_id": "model_test",
  "user_id": "1763038682578",
  "status": "completed",
  "predictions": {
    "1763038682578": [
      {"item_id": "5", "score": 5.0, "rank": 1},
      {"item_id": "2", "score": 1.0, "rank": 2},
      {"item_id": "4", "score": 1.0, "rank": 3}
    ]
  },
  "recommendations": [
    {"item_id": "5", "score": 5.0, "rank": 1},
    {"item_id": "2", "score": 1.0, "rank": 2},
    {"item_id": "4", "score": 1.0, "rank": 3}
  ],
  "count": 3
}
```

### Dashboard Display

The recommendations section should show:
- ✅ Product cards with full details (name, description, price)
- ✅ Category badges
- ✅ AI Score and Rank information
- ✅ Like buttons
- ✅ Success message showing count

## 🐛 Troubleshooting

### Issue: "No recommendations available yet"

**Possible Causes:**
1. User ID not in training data (cold start problem)
2. Model not trained with demo website data
3. Wrong model_id

**Solutions:**
```bash
# Check if user has interactions
curl "http://localhost:3500/api/user/actions"

# Train model with demo data
docker exec vrecom_ai_server python3 /app/train_demo_model.py

# Use correct model_id in dashboard
# Change line in dashboard.ejs:
const response = await fetch('/api/recommendations?model_id=model_test&n=5');
```

### Issue: "Failed to load recommendations"

**Possible Causes:**
1. AI server not running
2. API server not running
3. Network issues

**Solutions:**
```bash
# Check services
docker-compose ps

# Check AI server logs
docker logs vrecom_ai_server -f

# Check API server logs
docker logs vrecom_api_server -f

# Restart services if needed
docker-compose restart ai_server api_server
```

### Issue: Products show as "Product #X" without details

**Possible Causes:**
1. Product IDs in recommendations don't match products.json
2. Products data not loaded

**Solutions:**
```bash
# Check products file
cat tests/demo-website/data/products.json

# Verify product IDs match recommended item_ids
# Add missing products if needed
```

## 📝 Configuration

### Change Default Model

Edit `server.js` line ~203:

```javascript
const modelId = req.query.model_id || 'model_test'; // Change 'model_test' to your model
```

### Change Number of Recommendations

Edit `dashboard.ejs` line ~297:

```javascript
const response = await fetch('/api/recommendations?model_id=model_test&n=5'); // Change n=5
```

### Add More Products

Edit `tests/demo-website/data/products.json`:

```json
[
  {
    "id": 6,
    "name": "New Product",
    "description": "Description here",
    "price": 199,
    "category": "electronics"
  }
]
```

Then restart demo website.

## 🎓 Understanding the Data Flow

1. **User Interaction** → Like/view product → Saved to `user_actions.json`
2. **Training** → Script reads `user_actions.json` → Trains model → Saves to `models/`
3. **Recommendation Request** → Frontend → Demo Website API → API Server → AI Server
4. **Response Transform** → AI Server returns predictions → API Server passes through → Demo Website transforms to `recommendations` array
5. **Display** → Frontend extracts recommendations → Fetches product details → Renders cards

## 🔄 Complete Testing Workflow

### Step 1: Setup

```bash
# Start all services
start.cmd

# Start demo website
cd tests\demo-website
npm install
npm start
```

### Step 2: Create Test Data

1. Open `http://localhost:3500`
2. Login with any username/password
3. Like at least 3-5 products
4. View some products

### Step 3: Train Model

```bash
# Copy data and train
docker cp tests\demo-website\data\user_actions.json vrecom_ai_server:/app/
docker exec vrecom_ai_server python3 /app/train_demo_model.py
```

### Step 4: Test Display

1. Refresh dashboard: `http://localhost:3500/dashboard`
2. Check "AI Recommendations" section
3. Should see product cards with scores

### Step 5: Debug if Needed

```bash
# Check API response
curl "http://localhost:3500/api/recommendations?model_id=demo_model&n=5"

# Check browser console for errors
# Open DevTools > Console

# Check server logs
# Demo website terminal shows request logs
```

## 📚 Related Files

- `server.js` - Backend API transformation
- `views/dashboard.ejs` - Frontend display logic
- `test-recommendations.html` - Standalone test page
- `../scripts/train_demo_model.py` - Model training script
- `../../HUONG_DAN_TRAIN_MODEL.md` - Training guide (Vietnamese)

## 💡 Tips

1. **Always check browser console** for detailed error messages
2. **Use test-recommendations.html** for quick debugging without authentication
3. **Train model with demo data** before expecting recommendations
4. **Verify user_id** matches between demo website and model training
5. **Check model_id** parameter - must match trained model name

---

**✅ If everything works correctly, you should see:**
- Product cards in "AI Recommendations" section
- Full product details (name, price, description)
- AI Score and Rank for each recommendation
- Green success message with count

**❌ If you see empty state:**
- User not in training data → Train model with current user data
- Model not found → Check model_id parameter
- API server down → Restart services

---

**Last Updated:** 2025-11-15
**Version:** 1.0