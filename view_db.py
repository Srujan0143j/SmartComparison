import os
import json
from pymongo import MongoClient
from bson import ObjectId

# Handle ObjectId serialization for clean terminal output
class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

def main():
    # Load URI from env, fallback to local
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "smartcompare_db")

    print("=" * 60)
    print(f" Connecting to: {mongo_uri}")
    print(f" Database: {db_name}")
    print("=" * 60)

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        # Verify connection
        client.server_info()
        db = client[db_name]
        products_col = db["products"]
        
        # Get total count
        total_products = products_col.count_documents({})
        print("\n[SUCCESS] Connection Successful!")
        print(f"Total Documents in 'products' collection: {total_products}")
        
        if total_products == 0:
            print("[WARNING] The database is currently empty. Run the backend or seed script to populate it.")
            return

        print("\nCategories Summary:")
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}}
        ]
        categories = list(products_col.aggregate(pipeline))
        for cat in categories:
            print(f"  * {cat['_id'] or 'No Category'}: {cat['count']} items")

        # Show sample product
        print("\nSample Product Document Preview:")
        sample = products_col.find_one()
        if sample:
            formatted_json = json.dumps(sample, indent=4, cls=MongoEncoder)
            # Limit printed reviews so it doesn't flood the terminal
            lines = formatted_json.split("\n")
            if len(lines) > 40:
                print("\n".join(lines[:40]))
                print("    ... [Reviews and remaining fields truncated for display] ...")
                print("}")
            else:
                print(formatted_json)

        print("\nTip: To see all documents, install MongoDB Compass (GUI) or run MongoDB Atlas Browse Collections.")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed to connect to MongoDB: {e}")
        print("Please ensure MongoDB is running locally or check your MONGO_URI string.")
        print("=" * 60)

if __name__ == "__main__":
    main()
