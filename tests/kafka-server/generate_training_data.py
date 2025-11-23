#!/usr/bin/env python3
"""
Training Data Generator for VRecommendation
===========================================
Generate large realistic datasets for training recommendation models.

Features:
- Realistic user behavior patterns
- Item popularity distributions
- User preference clustering
- Temporal dynamics
- Cold start scenarios
- Diverse rating distributions

Usage:
    python generate_training_data.py
"""

import csv
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from confluent_kafka import Producer


class TrainingDataGenerator:
    """Generate realistic training data for recommendation systems."""

    def __init__(
        self,
        num_users: int = 200,
        num_items: int = 500,
        num_interactions: int = 10000,
    ):
        self.num_users = num_users
        self.num_items = num_items
        self.num_interactions = num_interactions

        # Generate users and items
        self.users = [f"user_{i}" for i in range(1, num_users + 1)]
        self.items = [f"item_{i}" for i in range(1, num_items + 1)]

        # Define item categories (20% each)
        category_size = num_items // 5
        self.item_categories = {
            "electronics": self.items[0:category_size],
            "fashion": self.items[category_size : category_size * 2],
            "home": self.items[category_size * 2 : category_size * 3],
            "sports": self.items[category_size * 3 : category_size * 4],
            "books": self.items[category_size * 4 :],
        }

        # Popular items (top 10%)
        popular_count = max(10, num_items // 10)
        self.popular_items = self.items[:popular_count]

        # Create user clusters (users with similar preferences)
        self.user_clusters = self._create_user_clusters()

        # User preference profiles
        self.user_preferences = self._create_user_preferences()

        # Statistics
        self.stats = {
            "users": num_users,
            "items": num_items,
            "interactions": 0,
            "avg_rating": 0.0,
            "rating_distribution": {},
        }

    def _create_user_clusters(self) -> Dict[str, List[str]]:
        """Create user clusters with similar preferences."""
        clusters = {
            "tech_enthusiasts": [],
            "fashion_lovers": [],
            "home_makers": [],
            "sports_fans": [],
            "bookworms": [],
            "general": [],
        }

        for user in self.users:
            # Assign users to clusters with some randomness
            rand = random.random()
            if rand < 0.15:
                clusters["tech_enthusiasts"].append(user)
            elif rand < 0.30:
                clusters["fashion_lovers"].append(user)
            elif rand < 0.45:
                clusters["home_makers"].append(user)
            elif rand < 0.60:
                clusters["sports_fans"].append(user)
            elif rand < 0.75:
                clusters["bookworms"].append(user)
            else:
                clusters["general"].append(user)

        return clusters

    def _create_user_preferences(self) -> Dict[str, List[str]]:
        """Create user preference profiles based on clusters."""
        preferences = {}

        for cluster_name, users in self.user_clusters.items():
            for user in users:
                if cluster_name == "tech_enthusiasts":
                    # Prefer electronics
                    preferred = random.sample(
                        self.item_categories["electronics"],
                        min(10, len(self.item_categories["electronics"])),
                    )
                elif cluster_name == "fashion_lovers":
                    # Prefer fashion
                    preferred = random.sample(
                        self.item_categories["fashion"],
                        min(10, len(self.item_categories["fashion"])),
                    )
                elif cluster_name == "home_makers":
                    # Prefer home items
                    preferred = random.sample(
                        self.item_categories["home"],
                        min(10, len(self.item_categories["home"])),
                    )
                elif cluster_name == "sports_fans":
                    # Prefer sports
                    preferred = random.sample(
                        self.item_categories["sports"],
                        min(10, len(self.item_categories["sports"])),
                    )
                elif cluster_name == "bookworms":
                    # Prefer books
                    preferred = random.sample(
                        self.item_categories["books"],
                        min(10, len(self.item_categories["books"])),
                    )
                else:
                    # General users: random items
                    preferred = random.sample(self.items, min(15, len(self.items)))

                preferences[user] = preferred

        return preferences

    def generate_interaction(
        self, base_timestamp: datetime, interaction_id: int
    ) -> Dict[str, Any]:
        """Generate a single realistic interaction."""
        # User selection (80-20 rule: 20% users create 80% interactions)
        if random.random() < 0.8:
            # Active users (first 20%)
            user_id = random.choice(self.users[: len(self.users) // 5])
        else:
            # Regular users
            user_id = random.choice(self.users)

        # Item selection based on multiple factors
        item_id = self._select_item_for_user(user_id)

        # Rating based on user preference
        rating = self._generate_rating(user_id, item_id)

        # Timestamp with variance (spread over 30 days)
        days_offset = random.randint(0, 30)
        hours_offset = random.randint(0, 23)
        minutes_offset = random.randint(0, 59)
        timestamp = base_timestamp + timedelta(
            days=days_offset, hours=hours_offset, minutes=minutes_offset
        )

        return {
            "user_id": user_id,
            "item_id": item_id,
            "rating": rating,
            "timestamp": timestamp.isoformat() + "Z",
            "interaction_id": interaction_id,
        }

    def _select_item_for_user(self, user_id: str) -> str:
        """Select item based on user preferences and item popularity."""
        rand = random.random()

        # 50% chance for user preferred items
        if user_id in self.user_preferences and rand < 0.50:
            return random.choice(self.user_preferences[user_id])

        # 30% chance for popular items
        elif rand < 0.80:
            return random.choice(self.popular_items)

        # 20% chance for random items (exploration)
        else:
            return random.choice(self.items)

    def _generate_rating(self, user_id: str, item_id: str) -> float:
        """Generate rating based on user-item match."""
        # Check if item is in user's preferred list
        is_preferred = (
            user_id in self.user_preferences
            and item_id in self.user_preferences[user_id]
        )

        # Check if item is popular
        is_popular = item_id in self.popular_items

        if is_preferred:
            # High ratings for preferred items (4.0-5.0)
            return random.choice([4.0, 4.5, 5.0])
        elif is_popular:
            # Good ratings for popular items (3.0-5.0)
            return random.choice([3.0, 3.5, 4.0, 4.5, 5.0])
        else:
            # Mixed ratings for other items (1.0-5.0)
            return random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])

    def generate_dataset(self) -> List[Dict[str, Any]]:
        """Generate complete dataset."""
        print(f"\nGenerating training dataset...")
        print(f"  Users: {self.num_users}")
        print(f"  Items: {self.num_items}")
        print(f"  Target interactions: {self.num_interactions}")
        print(f"  Item categories: {len(self.item_categories)}")
        print(f"  Popular items: {len(self.popular_items)}")
        print()

        interactions = []
        base_timestamp = datetime.utcnow() - timedelta(days=30)

        # Generate interactions
        for i in range(self.num_interactions):
            interaction = self.generate_interaction(base_timestamp, i + 1)
            interactions.append(interaction)

            # Progress indicator
            if (i + 1) % 1000 == 0:
                progress = (i + 1) / self.num_interactions * 100
                print(f"  Progress: {i + 1}/{self.num_interactions} ({progress:.1f}%)")

        print(f"\n✓ Generated {len(interactions)} interactions")

        # Calculate statistics
        self._calculate_statistics(interactions)

        return interactions

    def _calculate_statistics(self, interactions: List[Dict[str, Any]]):
        """Calculate dataset statistics."""
        self.stats["interactions"] = len(interactions)

        ratings = [i["rating"] for i in interactions]
        self.stats["avg_rating"] = sum(ratings) / len(ratings)

        # Rating distribution
        rating_dist = {}
        for rating in ratings:
            rating_dist[rating] = rating_dist.get(rating, 0) + 1
        self.stats["rating_distribution"] = rating_dist

        # Unique users and items
        unique_users = set(i["user_id"] for i in interactions)
        unique_items = set(i["item_id"] for i in interactions)
        self.stats["unique_users"] = len(unique_users)
        self.stats["unique_items"] = len(unique_items)

        # Interactions per user
        user_interactions = {}
        for i in interactions:
            user_id = i["user_id"]
            user_interactions[user_id] = user_interactions.get(user_id, 0) + 1

        self.stats["avg_interactions_per_user"] = sum(user_interactions.values()) / len(
            user_interactions
        )
        self.stats["max_interactions_per_user"] = max(user_interactions.values())
        self.stats["min_interactions_per_user"] = min(user_interactions.values())

    def print_statistics(self):
        """Print dataset statistics."""
        print("\n" + "=" * 70)
        print("Dataset Statistics")
        print("=" * 70)
        print(f"Total Users: {self.stats['users']}")
        print(f"Total Items: {self.stats['items']}")
        print(f"Total Interactions: {self.stats['interactions']}")
        print(f"Unique Active Users: {self.stats.get('unique_users', 0)}")
        print(f"Unique Items with Interactions: {self.stats.get('unique_items', 0)}")
        print(f"\nAverage Rating: {self.stats['avg_rating']:.2f}")
        print(
            f"Avg Interactions per User: {self.stats.get('avg_interactions_per_user', 0):.2f}"
        )
        print(
            f"Max Interactions per User: {self.stats.get('max_interactions_per_user', 0)}"
        )
        print(
            f"Min Interactions per User: {self.stats.get('min_interactions_per_user', 0)}"
        )

        print("\nRating Distribution:")
        for rating in sorted(self.stats["rating_distribution"].keys()):
            count = self.stats["rating_distribution"][rating]
            percentage = (count / self.stats["interactions"]) * 100
            print(f"  {rating:.1f}: {count:5d} ({percentage:5.2f}%)")
        print("=" * 70)

    def save_to_csv(self, filename: str = "training_data.csv"):
        """Save dataset to CSV file."""
        filepath = Path(__file__).parent / filename
        interactions = self.generate_dataset()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["user_id", "item_id", "rating", "timestamp"]
            )
            writer.writeheader()
            for interaction in interactions:
                writer.writerow(
                    {
                        "user_id": interaction["user_id"],
                        "item_id": interaction["item_id"],
                        "rating": interaction["rating"],
                        "timestamp": interaction["timestamp"],
                    }
                )

        print(f"\n✓ Saved to CSV: {filepath}")
        self.print_statistics()

    def save_to_json(self, filename: str = "training_data.json"):
        """Save dataset to JSON file."""
        filepath = Path(__file__).parent / filename
        interactions = self.generate_dataset()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "generated_at": datetime.utcnow().isoformat() + "Z",
                        "num_users": self.num_users,
                        "num_items": self.num_items,
                        "num_interactions": len(interactions),
                    },
                    "interactions": interactions,
                    "statistics": self.stats,
                },
                f,
                indent=2,
            )

        print(f"\n✓ Saved to JSON: {filepath}")
        self.print_statistics()

    def send_to_kafka(
        self, broker: str = "localhost:9092", topic: str = "interactions"
    ):
        """Send dataset to Kafka topic."""
        print(f"\n{'=' * 70}")
        print("Sending to Kafka")
        print("=" * 70)
        print(f"Broker: {broker}")
        print(f"Topic: {topic}")

        interactions = self.generate_dataset()

        # Create producer
        config = {"bootstrap.servers": broker, "client.id": "training-data-generator"}
        producer = Producer(config)

        delivery_count = {"success": 0, "failed": 0}

        def delivery_callback(err, msg):
            if err:
                delivery_count["failed"] += 1
            else:
                delivery_count["success"] += 1

        print("\nSending messages to Kafka...")
        for i, interaction in enumerate(interactions):
            try:
                message = json.dumps(
                    {
                        "user_id": interaction["user_id"],
                        "item_id": interaction["item_id"],
                        "rating": interaction["rating"],
                        "timestamp": interaction["timestamp"],
                    }
                ).encode("utf-8")

                producer.produce(
                    topic=topic,
                    key=interaction["user_id"].encode("utf-8"),
                    value=message,
                    callback=delivery_callback,
                )

                producer.poll(0)

                # Progress indicator
                if (i + 1) % 1000 == 0:
                    print(f"  Sent: {i + 1}/{len(interactions)}")

            except Exception as e:
                print(f"ERROR sending message {i + 1}: {e}")
                delivery_count["failed"] += 1

        # Flush remaining messages
        print("\nFlushing remaining messages...")
        producer.flush()

        print(f"\n✓ Kafka delivery complete!")
        print(f"  Successful: {delivery_count['success']}")
        print(f"  Failed: {delivery_count['failed']}")
        self.print_statistics()


def main():
    """Main function."""
    print("\n" + "=" * 70)
    print("VRecommendation Training Data Generator")
    print("=" * 70)

    print("\nConfiguration:")
    try:
        num_users = int(input("Number of users (default: 200): ") or "200")
        num_items = int(input("Number of items (default: 500): ") or "500")
        num_interactions = int(
            input("Number of interactions (default: 10000): ") or "10000"
        )
    except ValueError:
        print("Invalid input. Using defaults.")
        num_users, num_items, num_interactions = 200, 500, 10000

    generator = TrainingDataGenerator(num_users, num_items, num_interactions)

    print("\nOutput format:")
    print("1. Save to CSV file")
    print("2. Save to JSON file")
    print("3. Send to Kafka")
    print("4. All of the above")

    choice = input("\nEnter choice (1-4): ").strip()

    try:
        if choice == "1":
            filename = input("CSV filename (default: training_data.csv): ").strip()
            if not filename:
                filename = "training_data.csv"
            generator.save_to_csv(filename)

        elif choice == "2":
            filename = input("JSON filename (default: training_data.json): ").strip()
            if not filename:
                filename = "training_data.json"
            generator.save_to_json(filename)

        elif choice == "3":
            broker = input("Kafka broker (default: localhost:9092): ").strip()
            if not broker:
                broker = "localhost:9092"
            topic = input("Kafka topic (default: interactions): ").strip()
            if not topic:
                topic = "interactions"
            generator.send_to_kafka(broker, topic)

        elif choice == "4":
            print("\n🚀 Generating all outputs...")

            # CSV
            generator_csv = TrainingDataGenerator(
                num_users, num_items, num_interactions
            )
            generator_csv.save_to_csv("training_data.csv")

            # JSON
            generator_json = TrainingDataGenerator(
                num_users, num_items, num_interactions
            )
            generator_json.save_to_json("training_data.json")

            # Kafka
            broker = input("\nKafka broker (default: localhost:9092): ").strip()
            if not broker:
                broker = "localhost:9092"
            topic = input("Kafka topic (default: interactions): ").strip()
            if not topic:
                topic = "interactions"

            generator_kafka = TrainingDataGenerator(
                num_users, num_items, num_interactions
            )
            generator_kafka.send_to_kafka(broker, topic)

            print("\n✓ All outputs generated successfully!")

        else:
            print("Invalid choice. Exiting.")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()

    print("\nDone!")


if __name__ == "__main__":
    main()
