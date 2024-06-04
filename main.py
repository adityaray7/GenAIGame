import pygame
import random
from villager import Villager
from task_manager import assign_tasks_to_villagers_from_llm, initialize_task_locations,assign_next_task
import json
from utils.gpt_query import get_query
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
import time
from interactions import handle_villager_interactions
from threading import Thread

load_dotenv()
# # Initialize LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")


# Multithreading 
villagers_threaded = []

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
CLEAR_CONVERSATIONS_INTERVAL = 10  # Number of iterations before clearing conversations


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()


# Load background image
background_image = pygame.image.load("images/map2.png")
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))


# Predefined backgrounds for villagers
backgrounds = [
    ["I am Villager 0.", "I enjoy exploring the woods and gathering herbs.", "I often cook meals for my fellow villagers."],
    ["I am Villager 1.", "I have a knack for construction and enjoy building structures.", "I believe a sturdy village is key to our safety."],
    ["I am Villager 2.", "I am always on high alert, watching over the village day and night.", "I take pride in keeping everyone safe from harm."]
    # ["I am Villager 3.", "I am drawn to the river, where I find peace and serenity.", "I am the one who fetches water for the village."],
    # ["I am Villager 4.", "I am passionate about culinary arts and experimenting with flavors.", "I love to create delicious meals for my friends and family."],
    # ["I am Villager 5.", "I am a skilled hunter, trained to track and capture prey.", "I provide meat and hides to sustain our community."],
    # ["I am Villager 6.", "I am curious by nature and enjoy exploring new territories.", "I often venture into the unknown to gather information."],
    # ["I am Villager 7.", "I have a strong connection to nature and spend my days gathering wood and tending to the forest.", "I ensure we have enough resources to thrive."],
    # ["I am Villager 8.", "I possess knowledge of ancient healing techniques passed down through generations.", "I am the village healer, tending to the sick and injured."],
    # ["I am Villager 9.", "I am patient and compassionate, with a gift for teaching.", "I educate the children of our village, guiding them toward a brighter future."],
]

# Initialize villagers
villagers = []
for i in range(len(backgrounds)):
    x = random.randint(50, SCREEN_WIDTH - 50)
    y = random.randint(50, SCREEN_HEIGHT - 50)
    background_texts = backgrounds[i]
    villager = Villager(f"villager_{i}", x, y, background_texts)
    villager.last_talk_attempt_time = 0  # Initialize last talk attempt time
    villagers.append(villager)

def villager_info(villagers):
    info = []
    for villager in villagers:
        info.append({
            "agent_id": villager.agent_id,
            "x": villager.x,
            "y": villager.y,
            "current_task": villager.current_task,
            "task_start_time": villager.task_start_time,
            "task_end_time": villager.task_end_time,
            "task_doing": villager.task_doing,
            "talking": villager.talking
        })
    return info

def save_game_state(villagers, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(villager_info(villagers), f, indent=4)

# Function to save conversations to a JSON file
def save_conversations(conversations, filename="conversations.json"):
    with open(filename, 'w') as f:
        json.dump(conversations, f, indent=4)

    # conversations.clear()  # Clear conversations after saving


# Initialize task locations
task_locations = initialize_task_locations()

# Assign tasks to villagers from LLM
assign_tasks_to_villagers_from_llm(villagers, task_locations)
conversations = []  # List to store conversations

def assign_task_thread(villager):
    if (villager.agent_id in villagers_threaded):
        return
    villagers_threaded.append(villager.agent_id)
    print(f"{villager.agent_id} has completed the task '{villager.current_task}'!")
    print(f"{villagers_threaded} are the villagers currently getting assigned tasks")
    # Assign next task to the villager
    print(f"Assigning next task to {villager.agent_id}...")
    task_name, task_location = assign_next_task(villager, task_locations,villager.current_task)
    task_time = task_location.task_period  # Time required for the task
    villager.assign_task(task_name, task_location, task_time)  # Assign new task
    print(f"{villager.agent_id} is now assigned the task '{task_name}'... ({task_time} seconds)\n")
    villagers_threaded.remove(villager.agent_id)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update game state

    for villager in villagers:
        if villager.task_complete():
            x = Thread(target=assign_task_thread, args=(villager,))
            x.start()
            
        villager.update()

        # Handle villager interactions
    
    Thread(target=handle_villager_interactions, args=(villagers,conversations)).start()

    # Save game state periodically
    save_game_state(villagers)
    save_conversations(conversations)
    

    # Render game state
    screen.blit(background_image, (0, 0))  # Draw background image
    
    for villager in villagers:
        villager.draw(screen)
    for task_location in task_locations:
        task_location.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()