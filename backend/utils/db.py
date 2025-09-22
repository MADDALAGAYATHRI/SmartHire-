import os
from pymongo import MongoClient

_client = None

def get_db():
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)
    dbname = os.getenv("MONGO_DB","smarthire")
    return _client[dbname]
