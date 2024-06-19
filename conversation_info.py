import json
from utils.logger import logger
import os

# Function to load conversations from a JSON file
def load_conversations(filename="conversations.json"):

    if not os.path.exists(filename):
        print(f"Creating {filename} file...")
        with open(filename, "w") as f:
            json.dump([], f)

    with open(filename, 'r') as f:
        return json.load(f)

# Load conversations from the JSON file
conversations = load_conversations()


if __name__ == "__main__":
    # Print conversations
    for conversation in conversations:
        logger.info(f"{conversation['villager1']} and {conversation['villager2']} conversation: {conversation['conversation']}")

    