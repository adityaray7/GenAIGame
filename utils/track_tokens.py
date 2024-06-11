import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import datetime
from utils.logger import logger
from pymongo import MongoClient

load_dotenv(".env")

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

# Connect to your Atlas cluster
client = MongoClient(ATLAS_CONNECTION_STRING)

# Define collection and index name
db_name = "langchain_db"
collection_name = "token_tracking"
atlas_collection = client[db_name][collection_name]

def token_tracker(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)

        usage_info = {
            "completion": response.content,
            "completion_tokens": response.response_metadata["token_usage"]["completion_tokens"],
            "prompt_tokens": response.response_metadata["token_usage"]["prompt_tokens"],
            "total_tokens": response.response_metadata["token_usage"]["total_tokens"],
            "model_name": response.response_metadata["model_name"],
            "time": datetime.datetime.now()
        }

        if usage_info["model_name"] == "gpt-35-turbo":
            usage_info["cost"] = 0.5*10e-6 * usage_info["prompt_tokens"] + 1.5*10e-6 * usage_info["completion_tokens"]
            usage_info['cost'] = round(usage_info['cost'],9)
        
        atlas_collection.insert_one(usage_info)

        return response.content.strip()
    return wrapper
