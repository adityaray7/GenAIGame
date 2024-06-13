from pymongo import MongoClient
import os

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

def create_mongo_client():
    client = MongoClient(ATLAS_CONNECTION_STRING)
    return client

def get_atlas_collection(db_name, collection_name):
    client = create_mongo_client()
    collection = client[db_name][collection_name]
    
    
    # if collection_name == "conversations":
    #     collection.delete_many({})
    
    return collection



