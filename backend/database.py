import os
import json
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smartcompare_db")
IS_VERCEL = "VERCEL" in os.environ

client = None
db = None

def get_db():
    global client, db
    if db is None:
        # If running on Vercel and no cloud database URI is set, skip connection timeout and use JSON fallback
        if IS_VERCEL and (not MONGO_URI or "localhost" in MONGO_URI):
            print("Running on Vercel without cloud MongoDB URI. Falling back to local JSON file.")
            db = MockDB()
            return db
            
        try:
            # Connect with a short timeout to fail fast if local mongo isn't running
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            # Trigger connection call to verify server is up
            client.server_info()
            db = client[DB_NAME]
            print(f"Connected successfully to MongoDB at {MONGO_URI}, database: {DB_NAME}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            print("Fallback: Using local products.json file because MongoDB was not reachable.")
            # We will create a local fallback loaded from products.json
            db = MockDB()
    return db

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = []
    
    def find(self, filter_dict=None, projection=None):
        filter_dict = filter_dict or {}
        results = []
        for doc in self.data:
            if self._match_doc(doc, filter_dict):
                results.append(doc)
        return results

    def find_one(self, filter_dict):
        results = self.find(filter_dict)
        return results[0] if results else None

    def insert_one(self, document):
        # assign an ID
        if "_id" not in document:
            document["_id"] = str(len(self.data) + 1)
        self.data.append(document)
        return type('InsertOneResult', (object,), {'inserted_id': document["_id"]})

    def insert_many(self, documents):
        inserted_ids = []
        for doc in documents:
            res = self.insert_one(doc)
            inserted_ids.append(res.inserted_id)
        return type('InsertManyResult', (object,), {'inserted_ids': inserted_ids})

    def delete_many(self, filter_dict):
        before_len = len(self.data)
        self.data = [doc for doc in self.data if not self._match_doc(doc, filter_dict)]
        return type('DeleteResult', (object,), {'deleted_count': before_len - len(self.data)})

    def _match_doc(self, doc, filter_dict):
        for k, v in filter_dict.items():
            if k == "$or":
                # Any condition in the $or list must match
                any_match = False
                for cond in v:
                    cond_match = True
                    for cond_k, cond_v in cond.items():
                        if not self._match_field(doc.get(cond_k), cond_v):
                            cond_match = False
                            break
                    if cond_match:
                        any_match = True
                        break
                if not any_match:
                    return False
            else:
                if not self._match_field(doc.get(k), v):
                    return False
        return True

    def _match_field(self, field_value, condition):
        if isinstance(condition, dict) and "$regex" in condition:
            import re
            pattern = condition["$regex"]
            flags = re.IGNORECASE if "i" in condition.get("$options", "") else 0
            return bool(re.search(pattern, str(field_value or ""), flags))
        return field_value == condition

    def count_documents(self, filter_dict):
        return len(self.find(filter_dict))

class MockDB:
    def __init__(self):
        self.collections = {}
        # Prepopulate products collection from products.json if it exists
        products_col = MockCollection("products")
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, "products.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    products_col.data = json.load(f)
                print(f"Fallback database: Loaded {len(products_col.data)} products from local JSON file.")
            else:
                print("Fallback warning: products.json file not found.")
        except Exception as e:
            print(f"Fallback warning: Error loading products.json: {e}")
        
        self.collections["products"] = products_col

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

