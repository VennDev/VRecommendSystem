# Task & Model Workflow

## Overview

The AI Server uses a task-based system to automatically train models on a schedule.

## File Structure

```
backend/ai_server/
├── models/                          # Model storage
│   ├── {model_id}.pkl              # Trained model binary
│   ├── {model_id}_config.json      # Model configuration
│   └── {model_id}_metadata.json    # Model metadata
├── tasks/                           # Task definitions
│   └── {task_name}.json            # Task configuration
└── config/
    └── restaurant_data.yaml         # Data Chef configurations
```

## Workflow

### 1. Create a Model

**API**: `POST /create_model`

**Request**:
```json
{
  "model_id": "my_model",
  "model_name": "My Recommendation Model",
  "algorithm": "nmf",
  "message": "Model description",
  "hyperparameters": {
    "n_components": 10,
    "max_iter": 200
  }
}
```

**Creates**:
- `models/my_model_config.json` - Model configuration
- Model is initialized but NOT trained yet

**Status**: `initializing` or ready for training

### 2. Create a Data Chef

**API**: `POST /create_data_chef_from_api`

**Request**:
```json
{
  "data_chef_id": "demo_data",
  "url": "http://localhost:3500/api/training/interactions",
  "rename_columns": ""
}
```

**Creates**:
- Entry in `config/restaurant_data.yaml`
- Data source configuration

### 3. Add a Training Task

**API**: `POST /add_model_task`

**Request**:
```json
{
  "task_name": "train_my_model",
  "model_id": "my_model",
  "data_chef_id": "demo_data",
  "interval": 3600
}
```

**Creates**:
- `tasks/train_my_model.json` - Task configuration

**Task File Content**:
```json
{
  "task_name": "train_my_model",
  "model_id": "my_model",
  "interactions_data_chef_id": "demo_data",
  "user_features_data_chef_id": null,
  "item_features_data_chef_id": null,
  "interval": 3600
}
```

### 4. Restart Scheduler

**API**: `POST /restart_scheduler`

**Action**:
- Stops current scheduler
- Scans `tasks/` folder for all `.json` files
- For each task:
  - Reads task config from `tasks/{task_name}.json`
  - Reads model config from `models/{model_id}_config.json` (NEW: supports both `_config.json` and `.json`)
  - Schedules training job with specified interval

### 5. Training Execution

**Automatically runs at scheduled intervals**:

1. **Data Collection**:
   - Reads data from Data Chef (e.g., REST API)
   - Applies column mapping if specified
   - Validates data format

2. **Model Training**:
   - Initializes training session
   - Processes data in batches
   - Trains model with specified algorithm
   - Updates model status: `training` → `completed`

3. **Model Saving**:
   - Saves trained model to `models/{model_id}.pkl`
   - Updates `models/{model_id}_config.json` with metrics
   - Creates `models/{model_id}_metadata.json`

## Model Status States

- `initializing` - Model created, not trained yet
- `training` - Currently training
- `completed` - Training finished successfully
- `failed` - Training failed
- `stopped` - Training stopped manually
- `validating` - Model being validated

## Important Notes

### File Naming Convention

**CRITICAL**: The system now supports both file naming conventions:

1. **New convention** (preferred): `{model_id}_config.json`
2. **Old convention** (legacy): `{model_id}.json`

The task trainer will try `_config.json` first, then fall back to `.json` for backward compatibility.

### Scheduler Restart Requirement

**When to restart**:
- After adding a new task
- After modifying task intervals
- After updating task configurations
- After removing a task

**Why**: The scheduler loads tasks only at startup. Changes to task files are not picked up until restart.

### Data Format Requirements

For model training, data must have these columns:
- `user_id` (string/number) - User identifier
- `item_id` (string/number) - Item identifier
- `rating` (number, optional) - Interaction score (defaults to 1.0)

Use Data Chef's `rename_columns` to map your data format:
```
userId->user_id,productId->item_id,score->rating
```

## Troubleshooting

### "Model file not found" Error

**Old error**: `Model file not found: /app/models/model_test.json`

**Cause**: Task trainer was looking for `{model_id}.json` but model service creates `{model_id}_config.json`

**Fixed**: Task trainer now checks both file names

### Task Not Running

**Check**:
1. Task file exists in `tasks/` folder
2. Model config exists in `models/` folder (either `_config.json` or `.json`)
3. Scheduler has been restarted after adding task
4. Data Chef is properly configured
5. Check logs for errors

### Model Status Stuck on "training"

**Possible causes**:
- Data Chef returns empty data
- Data format is incorrect
- Training process crashed

**Check**:
- AI Server logs for error messages
- Data Chef URL is accessible
- Data format matches requirements

## API Endpoints Summary

### Models
- `POST /create_model` - Create new model
- `GET /list_models` - List all models
- `GET /get_model_info?model_id=xxx` - Get model details
- `DELETE /delete_model?model_id=xxx` - Delete model

### Data Chefs
- `POST /create_data_chef_from_csv` - CSV data source
- `POST /create_data_chef_from_sql` - SQL database
- `POST /create_data_chef_from_api` - REST API
- `GET /list_data_chefs` - List all data chefs
- `DELETE /delete_data_chef?data_chef_id=xxx` - Delete data chef

### Tasks
- `POST /add_model_task` - Add training task
- `POST /remove_model_task` - Remove task
- `GET /list_tasks` - List all tasks
- `POST /update_task_interval` - Update task interval

### Scheduler
- `POST /restart_scheduler` - Restart scheduler (picks up new tasks)
- `POST /stop_scheduler` - Stop scheduler
- `GET /get_scheduler_status` - Get scheduler status

### Recommendations
- `GET /recommend?user_id=xxx&model_id=yyy&n=10` - Get recommendations
