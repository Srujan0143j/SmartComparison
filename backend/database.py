import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "smartcompare_db")

client = None
db = None

def get_db():
    global client, db
    if db is None:
        try:
            # Connect with a short timeout to fail fast if local mongo isn't running
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
            # Trigger connection call to verify server is up
            client.server_info()
            db = client[DB_NAME]
            print(f"Connected successfully to MongoDB at {MONGO_URI}, database: {DB_NAME}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            print("Fallback: Using in-memory mock storage because MongoDB was not reachable.")
            # We will create a local in-memory fallback so the server doesn't crash 
            # and runs perfectly even if MongoDB isn't running on the developer machine yet.
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
            match = True
            for k, v in filter_dict.items():
                if k == "$or":
                    match = any(doc.get(sub_k) == sub_v for or_cond in v for sub_k, sub_v in or_cond.items())
                elif isinstance(v, dict) and "$regex" in v:
                    import re
                    pattern = v["$regex"]
                    flags = re.IGNORECASE if "i" in v.get("$options", "") else 0
                    if not re.search(pattern, str(doc.get(k, "")), flags):
                        match = False
                elif doc.get(k) != v:
                    match = False
            if match:
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
            if doc.get(k) != v:
                return False
        return True

    def count_documents(self, filter_dict):
        return len(self.find(filter_dict))

class MockDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]
