from pymongo import MongoClient
import os

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

def create_mongo_client():
    client = MongoClient(ATLAS_CONNECTION_STRING)
    return client

def get_atlas_collection(db_name, collection_name):
    client = create_mongo_client()
    db = client[db_name]
    

    if collection_name in db.list_collection_names():
        db[collection_name].drop()
    
    collection = db[collection_name]

    
    return collection



