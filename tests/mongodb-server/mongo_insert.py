import csv
import json
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, DuplicateKeyError

MONGO_URI = 'mongodb://admin:password123@localhost:27017/'
DATABASE_NAME = 'vrecom_test'
COLLECTION_NAME = 'interactions'

CSV_FILE = '../test-data/interactions.csv'

def connect_to_mongodb():
    """Connect to MongoDB and return database and collection."""
    try:
        client = MongoClient(MONGO_URI)
        client.admin.command('ping')
        print(f"Connected to MongoDB successfully")

        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        return client, db, collection
    except Exception as e:
        print(f"ERROR: Failed to connect to MongoDB: {e}")
        raise

def load_csv_data(csv_path):
    """Load interaction data from CSV file."""
    interactions = []
    csv_file_path = Path(__file__).parent / csv_path

    if not csv_file_path.exists():
        print(f"ERROR: CSV file not found at {csv_file_path}")
        return interactions

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            interactions.append({
                'user_id': row['user_id'],
                'item_id': row['item_id'],
                'rating': float(row['rating']),
                'timestamp': row['timestamp'],
                'created_at': datetime.utcnow()
            })

    print(f"Loaded {len(interactions)} interactions from CSV")
    return interactions

def insert_data(collection, interactions, batch_mode=True):
    """Insert interaction data into MongoDB."""
    print(f"\nInserting {len(interactions)} documents into MongoDB...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME}")
    print("-" * 60)

    if batch_mode:
        try:
            result = collection.insert_many(interactions, ordered=False)
            print(f"SUCCESS: Inserted {len(result.inserted_ids)} documents")
            return len(result.inserted_ids), 0

        except BulkWriteError as e:
            inserted = e.details['nInserted']
            errors = len(e.details['writeErrors'])
            print(f"Partial success: {inserted} inserted, {errors} duplicates skipped")
            return inserted, errors

    else:
        success_count = 0
        error_count = 0

        for idx, doc in enumerate(interactions, 1):
            try:
                collection.insert_one(doc)
                success_count += 1
                print(f"Inserted document {idx}/{len(interactions)}")

            except DuplicateKeyError:
                error_count += 1
                print(f"SKIP: Duplicate document {idx} (user: {doc['user_id']}, item: {doc['item_id']})")

            except Exception as e:
                error_count += 1
                print(f"ERROR: Failed to insert document {idx}: {e}")

        return success_count, error_count

def show_collection_stats(collection):
    """Display collection statistics."""
    count = collection.count_documents({})
    print("\n" + "=" * 60)
    print("COLLECTION STATISTICS")
    print("=" * 60)
    print(f"Total documents: {count}")

    if count > 0:
        unique_users = len(collection.distinct('user_id'))
        unique_items = len(collection.distinct('item_id'))

        print(f"Unique users: {unique_users}")
        print(f"Unique items: {unique_items}")

        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'avg_rating': {'$avg': '$rating'},
                    'min_rating': {'$min': '$rating'},
                    'max_rating': {'$max': '$rating'}
                }
            }
        ]

        stats = list(collection.aggregate(pipeline))
        if stats:
            print(f"Average rating: {stats[0]['avg_rating']:.2f}")
            print(f"Rating range: {stats[0]['min_rating']} - {stats[0]['max_rating']}")

        print("\nSample documents:")
        for doc in collection.find().limit(3):
            doc.pop('_id')
            doc.pop('created_at')
            print(f"  {json.dumps(doc, indent=2)}")

    print("=" * 60)

def query_examples(collection):
    """Run example queries."""
    print("\n" + "=" * 60)
    print("EXAMPLE QUERIES")
    print("=" * 60)

    print("\n1. Find all interactions for user001:")
    results = list(collection.find({'user_id': 'user001'}, {'_id': 0, 'created_at': 0}))
    print(f"   Found {len(results)} interactions")
    for r in results[:3]:
        print(f"   {json.dumps(r)}")

    print("\n2. Find high-rated items (rating >= 4.5):")
    results = list(collection.find({'rating': {'$gte': 4.5}}, {'_id': 0, 'created_at': 0}).limit(5))
    print(f"   Found {collection.count_documents({'rating': {'$gte': 4.5}})} interactions")
    for r in results:
        print(f"   {json.dumps(r)}")

    print("\n3. Count interactions per user:")
    pipeline = [
        {
            '$group': {
                '_id': '$user_id',
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    results = list(collection.aggregate(pipeline))
    for r in results:
        print(f"   {r['_id']}: {r['count']} interactions")

    print("=" * 60)

def clear_collection(collection):
    """Clear all documents from collection."""
    result = collection.delete_many({})
    print(f"\nCleared {result.deleted_count} documents from collection")

def main():
    """Main function."""
    print("\n" + "=" * 60)
    print("VRecommendation MongoDB Inserter")
    print("=" * 60)

    interactions = load_csv_data(CSV_FILE)

    if not interactions:
        print("ERROR: No data to insert. Exiting.")
        return

    try:
        client, db, collection = connect_to_mongodb()

        print("\nSelect operation:")
        print("1. Insert data (batch mode)")
        print("2. Insert data (one by one)")
        print("3. Clear collection and insert")
        print("4. Show collection stats")
        print("5. Run example queries")
        print("6. Clear collection only")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == '1':
            success, errors = insert_data(collection, interactions, batch_mode=True)
            print(f"\nInserted: {success}, Errors: {errors}")
            show_collection_stats(collection)

        elif choice == '2':
            success, errors = insert_data(collection, interactions, batch_mode=False)
            print(f"\nInserted: {success}, Errors: {errors}")
            show_collection_stats(collection)

        elif choice == '3':
            clear_collection(collection)
            success, errors = insert_data(collection, interactions, batch_mode=True)
            print(f"\nInserted: {success}, Errors: {errors}")
            show_collection_stats(collection)

        elif choice == '4':
            show_collection_stats(collection)

        elif choice == '5':
            query_examples(collection)

        elif choice == '6':
            clear_collection(collection)

        else:
            print("Invalid choice")

    except Exception as e:
        print(f"\nERROR: {e}")
    finally:
        print("\nClosing connection...")
        if 'client' in locals():
            client.close()
        print("Done!")

if __name__ == '__main__':
    main()
