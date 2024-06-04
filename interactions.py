'''
Currently not in use
'''


import random
from langchain_core.messages import HumanMessage, SystemMessage
from utils.gpt_query import get_query
from villager import Villager
import time
import json

TALK_DISTANCE_THRESHOLD = 50  # Adjust as needed
TALK_PROBABILITY = 0.05  # Adjust as needed
TALK_COOLDOWN_TIME = 30  # Time in seconds for cooldown period





# Method to handle villager interactions
def handle_villager_interactions(villagers,conversations):
    current_time = time.time()
    for villager1 in villagers:
        for villager2 in villagers:
            if villager1 != villager2:
                distance = ((villager1.x - villager2.x) ** 2 + (villager1.y - villager2.y) ** 2) ** 0.5
                if distance < TALK_DISTANCE_THRESHOLD and random.random() < TALK_PROBABILITY and current_time - villager1.last_talk_attempt_time >= TALK_COOLDOWN_TIME:
                    for i in range(random.randint(2, 4)):
                        context = " ".join(villager1.background_texts + villager2.background_texts)
                        
                        messages = [SystemMessage(content=context), HumanMessage(content="")]
                        response = get_query(messages)
                        # Add conversation to the list
                        conversations.append({"villager1": villager1.agent_id, "villager2": villager2.agent_id, "conversation": response})
                    # Update last talk attempt time for both villagers
                    villager1.last_talk_attempt_time = current_time
                    villager2.last_talk_attempt_time = current_time


