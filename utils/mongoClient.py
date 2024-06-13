from pymongo import MongoClient
import os

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

def create_mongo_client():
    client = MongoClient(ATLAS_CONNECTION_STRING)
    return client

def get_atlas_collection(db_name, collection_name):
    client = create_mongo_client()
    collection = client[db_name][collection_name]

    collection.delete_many({})
    return collection


def get_atlas_collections(db_name, collection_names):
    client = create_mongo_client()
    db = client[db_name]

    collections = []

    for collection_name in collection_names:
        collection = db[collection_name]
        # collection.delete_many({})
        collections.append(collection)
    
    return collections


    

