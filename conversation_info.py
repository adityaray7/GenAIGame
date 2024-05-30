import json

# Function to load conversations from a JSON file
def load_conversations(filename="conversations.json"):
    with open(filename, 'r') as f:
        return json.load(f)

# Load conversations from the JSON file
conversations = load_conversations()


if __name__ == "__main__":
    # Print conversations
    for conversation in conversations:
        print(f"{conversation['villager1']} and {conversation['villager2']} conversation: {conversation['conversation']}")

    