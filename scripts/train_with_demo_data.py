#!/usr/bin/env python3
"""
Script to train recommendation model with data from demo website.
This script reads interactions from the demo website and trains a new model.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configuration
DEMO_WEBSITE_URL = "http://localhost:3500"
AI_SERVER_URL = "http://localhost:9999"
MODEL_ID = "demo_model"
MODEL_TYPE = "svd"


def get_demo_interactions():
    """Get interaction data from demo website."""
    try:
        response = requests.get(
            f"{DEMO_WEBSITE_URL}/api/training/interactions", timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching interactions from demo website: {e}")
        print(f"Make sure demo website is running at {DEMO_WEBSITE_URL}")
        return None


def read_local_interactions(file_path):
    """Read interactions from local JSON file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Convert to training format
        interactions = []
        for action in data:
            interactions.append(
                {
                    "user_id": action["userId"],
                    "item_id": str(action["productId"]),
                    "rating": 5.0 if action["action"] == "like" else 1.0,
                    "timestamp": action["timestamp"],
                }
            )
        return interactions
    except Exception as e:
        print(f"Error reading local file {file_path}: {e}")
        return None


def train_model(interactions):
    """Train a new model with the interactions."""
    if not interactions or len(interactions) == 0:
        print("No interactions to train with!")
        return False

    print(f"\n📊 Training model with {len(interactions)} interactions...")
    print(f"   Unique users: {len(set(i['user_id'] for i in interactions))}")
    print(f"   Unique items: {len(set(i['item_id'] for i in interactions))}")

    # Prepare training data
    training_data = {
        "model_id": MODEL_ID,
        "model_name": "Demo Website Model",
        "message": "Trained with demo website data",
        "algorithm": MODEL_TYPE,
        "hyperparameters": {
            "n_components": 10,
            "algorithm": "randomized",
            "n_iter": 10,
            "random_state": 42,
        },
        "interaction_data": interactions,
    }

    try:
        # Initialize training
        print(f"\n🚀 Initializing training for model '{MODEL_ID}'...")
        response = requests.post(
            f"{AI_SERVER_URL}/api/v1/initialize_training",
            json=training_data,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ Training initialized: {result.get('status', 'unknown')}")

        # Train batch
        print(f"\n🔄 Training batch...")
        batch_response = requests.post(
            f"{AI_SERVER_URL}/api/v1/train_batch",
            json={"model_id": MODEL_ID, "interaction_data": interactions},
            timeout=60,
        )
        batch_response.raise_for_status()
        batch_result = batch_response.json()
        print(f"✅ Batch trained: {batch_result.get('status', 'unknown')}")

        # Finalize training
        print(f"\n🏁 Finalizing training...")
        finalize_response = requests.post(
            f"{AI_SERVER_URL}/api/v1/finalize_training",
            json={"model_id": MODEL_ID},
            timeout=60,
        )
        finalize_response.raise_for_status()
        finalize_result = finalize_response.json()

        print(f"\n✨ Model trained successfully!")
        print(f"   Model ID: {MODEL_ID}")
        print(f"   Status: {finalize_result.get('status', 'unknown')}")

        if "metrics" in finalize_result:
            metrics = finalize_result["metrics"]
            print(f"\n📈 Training Metrics:")
            print(f"   Training time: {metrics.get('training_time', 0):.2f}s")
            print(f"   Users: {metrics.get('n_users', 0)}")
            print(f"   Items: {metrics.get('n_items', 0)}")
            print(f"   Interactions: {metrics.get('n_interactions', 0)}")
            print(f"   Sparsity: {metrics.get('sparsity', 0):.2%}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error training model: {e}")
        if hasattr(e.response, "text"):
            print(f"   Response: {e.response.text}")
        return False


def test_recommendations(user_id):
    """Test recommendations for a user."""
    try:
        print(f"\n🔮 Testing recommendations for user {user_id}...")
        response = requests.get(
            f"{AI_SERVER_URL}/api/v1/recommend/{user_id}/{MODEL_ID}/5", timeout=10
        )
        response.raise_for_status()
        result = response.json()

        predictions = result.get("predictions", {}).get(user_id, [])
        if predictions:
            print(f"✅ Got {len(predictions)} recommendations:")
            for i, rec in enumerate(predictions, 1):
                print(f"   {i}. Item {rec['item_id']} (score: {rec['score']:.2f})")
        else:
            print(
                f"⚠️  No recommendations returned (user might not be in training data)"
            )

        return True
    except Exception as e:
        print(f"❌ Error testing recommendations: {e}")
        return False


def main():
    print("=" * 60)
    print("🎯 Demo Model Training Script")
    print("=" * 60)

    # Try to get interactions from demo website first
    interactions = get_demo_interactions()

    # If demo website is not running, try local file
    if not interactions:
        print("\n📁 Demo website not available, trying local file...")
        local_file = (
            Path(__file__).parent.parent
            / "tests"
            / "demo-website"
            / "data"
            / "user_actions.json"
        )
        if local_file.exists():
            print(f"   Reading from: {local_file}")
            interactions = read_local_interactions(local_file)
        else:
            print(f"❌ Local file not found: {local_file}")
            print("\nPlease either:")
            print("1. Start the demo website (npm start in tests/demo-website)")
            print("2. Ensure user_actions.json exists with interaction data")
            sys.exit(1)

    if not interactions:
        print("❌ No interaction data available!")
        sys.exit(1)

    # Train the model
    success = train_model(interactions)

    if success:
        # Test with first user
        user_ids = list(set(i["user_id"] for i in interactions))
        if user_ids:
            test_recommendations(user_ids[0])

        print("\n" + "=" * 60)
        print("✅ Training completed successfully!")
        print(f"   Model ID: {MODEL_ID}")
        print(f"   To get recommendations, use:")
        print(f"   GET {AI_SERVER_URL}/api/v1/recommend/<user_id>/{MODEL_ID}/10")
        print("=" * 60)
    else:
        print("\n❌ Training failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
