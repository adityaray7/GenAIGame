import openai
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import datetime
from logger import logger
from pymongo import MongoClient

load_dotenv(".env")

ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

# Connect to your Atlas cluster
client = MongoClient(ATLAS_CONNECTION_STRING)

# Define collection and index name
db_name = "langchain_db"
collection_name = "token_tracking"
atlas_collection = client[db_name][collection_name]

# Define track cost function
def track_tokens(response):
    content = response.content
    metadata = response.response_metadata
    token_usage = metadata['token_usage']
    # logger.debug("Tracking token usage...")

    token_tracking = {
        "completion": content,
        "completion_tokens": token_usage["completion_tokens"],
        "prompt_tokens": token_usage["prompt_tokens"],
        "total_tokens": token_usage["total_tokens"],
        "model_name": metadata["model_name"],
        "time": datetime.datetime.now()
    }

    if token_tracking["model_name"] == "gpt-35-turbo":
        token_tracking["cost"] = 0.5*10e-6 * token_tracking["prompt_tokens"] + 1.5*10e-6 * token_tracking["completion_tokens"]

    atlas_collection.insert_one(token_tracking)
    # logger.debug("Token usage tracked.")

# Save the response to the database
if __name__ == "__main__":
    response_dict = {
        "prompt": "test prompt",
        "response": "test response",
        "cost": 5
    }
    atlas_collection.insert_one(response_dict)
    print("Response saved to the database.")