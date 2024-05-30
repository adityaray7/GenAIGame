import random
from utils.gpt_query import get_query
from villager import Villager

def interact(villagers):
    for villager in villagers:
        # Randomly decide whether to talk or not
        rounds_to_talk = random.randint(0, 4)
        if rounds_to_talk > 0:
            # Choose a random number of rounds to talk
            for _ in range(rounds_to_talk):
                # Generate context from memory
                context = " ".join(villager.background_texts)
                # Generate a query to the LLM
                query = generate_query(villager)
                # Get response from LLM
                response = get_query([{"role": "system", "content": context}, {"role": "user", "content": query}])
                # Process response (if needed)
                process_response(response)

def generate_query(villager):
    # Generate a query based on the villager's background texts or any other relevant information
    # You can customize this based on your specific requirements
    return "Query generated based on villager's background"

def process_response(response):
    # Process the response obtained from the LLM
    # You can define your processing logic here
    pass
