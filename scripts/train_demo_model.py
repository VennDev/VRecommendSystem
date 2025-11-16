#!/usr/bin/env python3
"""
Simplified script to train recommendation model with demo website data.
This script is designed to run inside the AI server Docker container.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add the AI server source to path
sys.path.insert(0, "/app/src")

from ai_server.services.model_service import ModelService


def read_demo_interactions():
    """Read interactions from demo website data file."""
    # Try multiple possible paths
    possible_paths = [
        Path("/app/user_actions.json"),
        Path("/app/tests/demo-website/data/user_actions.json"),
        Path("../tests/demo-website/data/user_actions.json"),
        Path("tests/demo-website/data/user_actions.json"),
        Path("user_actions.json"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"📁 Reading interactions from: {path}")
            with open(path, "r") as f:
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

    print("❌ Could not find user_actions.json file!")
    return None


def train_model(interactions, model_id="demo_model"):
    """Train a new model with the interactions."""
    if not interactions or len(interactions) == 0:
        print("❌ No interactions to train with!")
        return False

    print("\n" + "=" * 60)
    print("🎯 Training Demo Model")
    print("=" * 60)
    print(f"\n📊 Training data summary:")
    print(f"   Total interactions: {len(interactions)}")
    print(f"   Unique users: {len(set(i['user_id'] for i in interactions))}")
    print(f"   Unique items: {len(set(i['item_id'] for i in interactions))}")

    # Show sample of interactions
    print(f"\n📝 Sample interactions:")
    for i in interactions[:3]:
        print(
            f"   User {i['user_id'][:10]}... → Item {i['item_id']} (rating: {i['rating']})"
        )
    if len(interactions) > 3:
        print(f"   ... and {len(interactions) - 3} more")

    try:
        # Initialize ModelService
        print(f"\n🚀 Initializing ModelService...")
        model_service = ModelService()

        # Prepare training configuration
        import pandas as pd

        interaction_df = pd.DataFrame(interactions)

        print(f"\n🔧 Configuring model '{model_id}'...")

        # Calculate appropriate n_components based on data size
        n_items = len(set(i["item_id"] for i in interactions))
        n_components = min(n_items - 1, 10)  # Must be less than n_items

        print(f"   Items in dataset: {n_items}")
        print(f"   Using n_components: {n_components}")

        hyperparameters = {
            "n_components": n_components,
            "algorithm": "randomized",
            "n_iter": 10,
            "random_state": 42,
            "tol": 0.0,
        }

        # Initialize training
        print(f"\n🔄 Initializing training session...")
        result = model_service.initialize_training(
            model_id=model_id,
            model_name="Demo Website Model",
            message="Trained with actual demo website interactions",
            algorithm="svd",
            hyperparameters=hyperparameters,
            model_type="svd",
        )

        status = (
            result.get("status")
            if isinstance(result, dict)
            else getattr(result, "status", None)
        )
        if status != "initialized":
            print(f"❌ Failed to initialize training: {result}")
            return False

        print(f"✅ Training initialized")

        # Train batch
        print(f"\n📦 Training batch...")
        batch_result = model_service.train_batch(
            model_id=model_id, interaction_data=interaction_df
        )

        batch_status = (
            batch_result.get("status")
            if isinstance(batch_result, dict)
            else getattr(batch_result, "status", None)
        )
        if batch_status not in ["training", "batch_processed"]:
            print(f"⚠️  Batch training status: {batch_status}")
        else:
            print(f"✅ Batch trained (status: {batch_status})")

        # Finalize training
        print(f"\n🏁 Finalizing training...")
        final_result = model_service.finalize_training(model_id=model_id)

        # Handle both dict and object responses
        if isinstance(final_result, dict):
            final_status = final_result.get("status")
            final_metrics = final_result.get("metrics", {})
        else:
            final_status = getattr(final_result, "status", None)
            final_metrics = getattr(final_result, "metrics", {})

        if final_status not in ["completed", "success"]:
            print(f"❌ Training failed with status: {final_status}")
            if isinstance(final_result, dict):
                print(f"   Error: {final_result.get('error', 'Unknown error')}")
            return False

        print(f"\n✨ Model trained successfully!")

        # Save the model
        print(f"\n💾 Saving model...")
        try:
            save_result = model_service.save_model(model_id=model_id)
            if isinstance(save_result, dict):
                save_status = save_result.get("status")
            else:
                save_status = getattr(save_result, "status", None)

            if save_status in ["success", "saved", "completed"]:
                print(f"✅ Model saved successfully")
            else:
                print(f"⚠️  Model save status: {save_status}")
        except Exception as e:
            print(f"⚠️  Error saving model: {e}")

        # Display metrics
        if final_metrics:
            print(f"\n📈 Training Metrics:")
            if isinstance(final_metrics, dict):
                print(f"   Training time: {final_metrics.get('training_time', 0):.3f}s")
                print(f"   Users: {final_metrics.get('n_users', 0)}")
                print(f"   Items: {final_metrics.get('n_items', 0)}")
                print(f"   Interactions: {final_metrics.get('n_interactions', 0)}")
                print(f"   Sparsity: {final_metrics.get('sparsity', 0):.2%}")
                if "explained_variance_ratio" in final_metrics:
                    print(
                        f"   Explained variance: {final_metrics.get('explained_variance_ratio', 0):.2%}"
                    )
            else:
                print(f"   Metrics: {final_metrics}")

        # Test recommendations
        user_ids = list(set(i["user_id"] for i in interactions))
        if user_ids:
            test_user = user_ids[0]
            print(f"\n🔮 Testing recommendations for user {test_user[:15]}...")

            pred_result = model_service.predict_recommendations(
                model_id=model_id, user_id=test_user, top_k=5
            )

            predictions = pred_result.predictions.get(test_user, [])
            if predictions:
                print(f"✅ Got {len(predictions)} recommendations:")
                for rec in predictions:
                    print(f"   → Item {rec['item_id']} (score: {rec['score']:.3f})")
            else:
                print(f"⚠️  No recommendations generated")

        print("\n" + "=" * 60)
        print("✅ Training completed successfully!")
        print(f"   Model ID: {model_id}")
        print(f"   Model path: models/{model_id}.pkl")
        print(f"\n💡 To get recommendations, use:")
        print(f"   GET /api/v1/recommend/<user_id>/{model_id}/10")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("🤖 Demo Website Model Training Script")
    print("=" * 60)

    # Read interactions
    interactions = read_demo_interactions()

    if not interactions:
        print("\n❌ No interaction data found!")
        print("\nMake sure the demo website has generated some user interactions.")
        print("The file should be at: tests/demo-website/data/user_actions.json")
        sys.exit(1)

    # Train the model
    success = train_model(interactions, model_id="demo_model")

    if not success:
        print("\n❌ Training failed!")
        sys.exit(1)

    print("\n✅ All done!")


if __name__ == "__main__":
    main()
