from utils.logger import logger
import pygame
import random

from task_manager import assign_tasks_to_villagers_from_llm, initialize_task_locations,assign_next_task,assign_first_task
import json
import os
from dotenv import load_dotenv
import time
from interactions import handle_villager_interactions,handle_meeting
from threading import Thread
from utils.to_be_threaded_function import threaded_function
from client import send
import math
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain_mongodb import MongoDBAtlasVectorSearch
load_dotenv()
from utils.mongoClient import get_atlas_collection
ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")

client_holder = {}
convo_holder = {}
# Define collection and index name
db_name = "langchain_db"
collection_name = "test"
convo_collection_name = "conversations"

vector_search_index = "vector_index"


# Connect to your Atlas cluster
mongo_connection_thread = Thread(target=threaded_function, args=(client_holder, get_atlas_collection, (db_name, collection_name)))
mongo_connection_thread.start()

# Connect to your Atlas cluster
convo_connection_thread = Thread(target=threaded_function, args=(convo_holder, get_atlas_collection, (db_name, convo_collection_name)))
convo_connection_thread.start()


from villager import Villager, Werewolf, Player
from utils.agentmemory import AgentMemory
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

# Multithreading 
villagers_threaded = []

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 720
DAY_DURATION = 120  # 60 seconds for a full day cycle
NIGHT_DURATION = 120  # 60 seconds for a full night cycle
TRANSITION_DURATION = 10  # 10 seconds for a transition period
MORNING_MEETING_DURATION = 10

# Load background images
background_day = pygame.image.load("images/map2.jpg")
background_night = pygame.image.load("images/night.jpg")
background_day = pygame.transform.scale(background_day, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_night = pygame.transform.scale(background_night, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Predefined backgrounds for villagers
backgrounds = [
    ["I am Sam. I enjoy exploring the woods and gathering herbs. The forest is my sanctuary, where I feel most alive and connected to nature.",
"I often cook meals for my fellow villagers. Using the herbs and plants I gather, I create nutritious and flavorful dishes that keep everyone in good health and spirits.",
"My knowledge of the forest's flora allows me to prepare remedies for common ailments, ensuring our village remains healthy and strong.","Keep an I eye on other villagers while taking and in the meeting raise your suspicion on the werewolf"],
    ["I am Jack. I have a knack for construction and enjoy building structures. From homes to storage sheds, my craftsmanship ensures our village is well-built and resilient.",
"I believe a sturdy village is key to our safety. By using strong materials and innovative designs, I create buildings that can withstand harsh weather and potential threats.",
"I also lead repair and maintenance efforts, making sure that every structure stands the test of time and continues to serve our community.","Keep an I eye on other villagers while taking and in the meeting raise your suspicion on the werewolf"
],
    ["I am Ronald. I am always on high alert, watching over the village day and night. My keen eyes and sharp senses make me an excellent guardian.",
"I take pride in keeping everyone safe from harm. Whether it's warding off wild animals or keeping an eye out for intruders, my vigilance ensures our village's security.",
"I train younger villagers in self-defense and alertness, passing on my knowledge so that they too can contribute to the safety of our home.","Keep an I eye on other villagers while taking and in the meeting raise your suspicion on the werewolf"]
    # ["I am Villager 3.", "I am drawn to the river, where I find peace and serenity.", "I am the one who fetches water for the village."],
    # ["I am Villager 4.", "I am passionate about culinary arts and experimenting with flavors.", "I love to create delicious meals for my friends and family."],
    # ["I am Villager 5.", "I am a skilled hunter, trained to track and capture prey.", "I provide meat and hides to sustain our community."],
    # ["I am Villager 6.", "I am curious by nature and enjoy exploring new territories.", "I often venture into the unknown to gather information."],
    # ["I am Villager 7.", "I have a strong connection to nature and spend my days gathering wood and tending to the forest.", "I ensure we have enough resources to thrive."],
    # ["I am Villager 8.", "I possess knowledge of ancient healing techniques passed down through generations.", "I am the village healer, tending to the sick and injured."],
    # ["I am Villager 9.", "I am patient and compassionate, with a gift for teaching.", "I educate the children of our village, guiding them toward a brighter future."],
]

names=["Sam","Jack","Ronald"]

werewolf_background = [
    ["I am Louis ","I am a werewolf and I am here to sabotage the tasks."],
    ["I am Harvey ","I am a werewolf and I am here to sabotage the tasks."]
]

llm = AzureChatOpenAI(
    azure_deployment="GPT35-turboA",
    api_version="2024-02-01",
    temperature=0
)


# Mongo connection thread
mongo_connection_thread.join()
atlas_collection = client_holder["result"]
convo_collection = convo_holder["result"]

def relevance_score_fn(score: float) -> float:
    """Return a similarity score on a scale [0, 1]."""
    # This will differ depending on a few things:
    # - the distance / similarity metric used by the VectorStore
    # - the scale of your embeddings (OpenAI's are unit norm. Many others are not!)
    # This function converts the euclidean norm of normalized embeddings
    # (0 is most similar, sqrt(2) most dissimilar)
    # to a similarity function (0 to 1)
    
    # this returns negetive relevance values so temporarily made abs()
    # change this to implement cosine_similarity
    return abs(1.0 - (score / math.sqrt(2)))

def create_new_memory_retriever():
    """Create a new vector store retriever unique to the agent."""
    # Define your embedding model
    embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding3",
        api_version="2024-02-01"
    )
    # Initialize the vectorstore as empty
    embedding_size = 3072

    ###############################################
    # index = faiss.IndexFlatL2(embedding_size)
    vectorstore = MongoDBAtlasVectorSearch(atlas_collection, embeddings_model)
    
    # vectorstore = FAISS(
    #     embedding_function=embeddings_model,
    #     index=index,
    #     docstore=InMemoryDocstore({}),
    #     index_to_docstore_id={},
    #     relevance_score_fn=relevance_score_fn,
    # )
    return TimeWeightedVectorStoreRetriever(
        vectorstore=vectorstore, other_score_keys=["importance"], k=15, decay_rate=0.005
    )

# Initialize villagers
villagers = []
num_villagers = len(backgrounds)
center_x = 800
center_y = 360
radius = 60

for i in range(num_villagers):
    angle = i * (2 * math.pi / num_villagers)
    x = int(center_x + radius * math.cos(angle))
    y = int(center_y + radius * math.sin(angle))
    background_texts = backgrounds[i]
    ". ".join(a for a in background_texts)
    villager_memory = AgentMemory(llm=llm, memory_retriever=create_new_memory_retriever())
    villager = Villager(names[i], random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT), background_texts=background_texts,llm=llm,memory=villager_memory,meeting_location=(x,y))
    villager.last_talk_attempt_time = 0  # Initialize last talk attempt time
    villagers.append(villager)

# for i in range(len(werewolf_background)):
#     x = random.randint(50, SCREEN_WIDTH - 50)
#     y = random.randint(50, SCREEN_HEIGHT - 50)
#     background_texts = backgrounds[i]
#     villager = Werewolf(f"werewolf_{i}", x, y, background_texts)
#     villager.last_talk_attempt_time = 0  # Initialize last talk attempt time
#     villagers.append(villager)

player_memory = AgentMemory(llm=llm, memory_retriever=create_new_memory_retriever())
player = Player("Player", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, ["I am the player."], llm,memory = player_memory, meeting_location=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))


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
# Function to save conversations to MongoDB
def save_conversations_to_mongodb(conversations):
    if conversations:
        convo_collection.insert_many(conversations)
        logger.info(f"Saved {len(conversations)} conversations to MongoDB.")
    else:
        logger.info("No new conversations to save.")

# Function to save conversations to a JSON file
def save_conversations(conversations, filename="conversations.json"):
    with open(filename, 'w') as f:
        json.dump(conversations, f, indent=4)


def blend_images(image1, image2, blend_factor):
    """Blend two images together based on the blend_factor (0.0 to 1.0)"""
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    temp_surface.blit(image1, (0, 0))
    temp_surface.set_alpha(int(255 * (1 - blend_factor)))
    screen.blit(temp_surface, (0, 0))
    
    temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    temp_surface.blit(image2, (0, 0))
    temp_surface.set_alpha(int(255 * blend_factor))
    screen.blit(temp_surface, (0, 0))

# Initialize task locations
task_locations = initialize_task_locations()

# Function to send game state to the 
def send_game_state():
    global villagers
    global is_day,blend_factor
    villagers_state = []
    num_villagers = len(villagers)
    for villager in villagers:
        villagers_state.append({
            "agent_id": villager.agent_id,
            "x": villager.x,
            "y": villager.y
        })

    global task_locations
    tasks = task_locations
    task_info = []
    for task in tasks:
        task_info.append({
            "x": task.x,
            "y": task.y,
            "task": task.task
        })
    
    conversations = []  
    with open ("conversations.json","r") as f:
        conversations = json.load(f)
        

    isConvo=False
    if conversations:
        isConvo=True  
      
    game_state = {
        "numVillagers": num_villagers,
        "villagers": villagers_state,
        "tasks": task_info, 
        "isDay": is_day,
        "blendFactor": blend_factor,
        "isConvo":isConvo,
        "conversations": conversations,
        
    }

    # convert game_state to json
    game_state = json.dumps(game_state)
    send(game_state)

# Assign tasks to villagers from LLM
# assign_tasks_to_villagers_from_llm(villagers, task_locations)
assign_first_task(villagers,task_locations,task_names=['Cook food','Build a house','Guard the village'])
conversations = []  # List to store conversations

def assign_task_thread(villager, current_task=None):
    if (villager.agent_id in villagers_threaded):
        return
    villagers_threaded.append(villager.agent_id)
    logger.info(f"{villager.agent_id} has completed the task '{current_task}'!")
    logger.info(f"{villagers_threaded} are the villagers currently getting assigned tasks")
    logger.debug(f"Assigning next task to {villager.agent_id}...")

    task_name, task_location = assign_next_task(villager, task_locations, current_task)
    task_time = task_location.task_period  # Time required for the task
    villager.assign_task(task_name, task_location, task_time)
    logger.info(f"{villager.agent_id} is now assigned the task '{task_name}'... ({task_time} seconds)\n")
    villagers_threaded.remove(villager.agent_id)


def morning_meeting(villagers,conversations,elapsed_time):
    global is_morning_meeting
    is_morning_meeting = True
    global reached
    reached = True
    temp = elapsed_time
    for villager in villagers:
        villager.interrupt_task()
        dx, dy = villager.meeting_location[0] - villager.x, villager.meeting_location[1] - villager.y
        dist = (dx**2 + dy**2)**0.5
        if dist > 1:
            villager.x += dx / dist
            villager.y += dy / dist
            reached = False
                
    if reached:
        logger.info("All villagers have gathered for the morning meeting.")
        handle_meeting(villagers, conversations)
        elapsed_time = temp
        return elapsed_time + MORNING_MEETING_DURATION
    
    return elapsed_time
    

def end_morning_meeting(villagers):
    global is_morning_meeting
    is_morning_meeting = False
    assign_first_task(villagers, task_locations, ['Cook food','Build a house','Guard the village'])


# Main game loop
running = True
start_time = time.time()
is_day = True
blend_factor = 0
is_morning_meeting = False

while running:
    
    send_game_state()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update()

    # Update day/night cycle
    curr = time.time()
    elapsed_time = curr - start_time
    blend_factor = 0


    if is_day:

        if elapsed_time >= DAY_DURATION:
            is_day = False
            start_time = curr
        elif elapsed_time >= DAY_DURATION - TRANSITION_DURATION:
            blend_factor = (elapsed_time - (DAY_DURATION - TRANSITION_DURATION)) / TRANSITION_DURATION

        if elapsed_time < MORNING_MEETING_DURATION:
            
            if not is_morning_meeting:
                logger.info("Starting morning meeting...")

            elapsed_time = morning_meeting(villagers,conversations,elapsed_time)


        elif elapsed_time > MORNING_MEETING_DURATION and is_morning_meeting:
            logger.info("Ending morning meeting...")
            temp = elapsed_time
            end_morning_meeting(villagers)
            elapsed_time = temp    

    
    else:
        if elapsed_time >= NIGHT_DURATION:
            is_day = True
            start_time = curr
        elif elapsed_time >= NIGHT_DURATION - TRANSITION_DURATION:
            blend_factor = (elapsed_time - (NIGHT_DURATION - TRANSITION_DURATION)) / TRANSITION_DURATION

    for villager in villagers:
        if villager.task_complete():
            current_task = villager.current_task
            thread = Thread(target=assign_task_thread, args=(villager,current_task,))
            thread.start()
            
        villager.update()

        # Handle villager interactions
    
    Thread(target=handle_villager_interactions, args=(player,villagers,conversations)).start()

    # Save game state periodically
    save_game_state(villagers)
    save_conversations(conversations)
    if conversations:
        print("conversations",conversations)
        save_conversations_to_mongodb(conversations)
    conversations.clear()  # Clear the list after saving
    
    # Render game state
    if is_day:
        blend_images(background_day, background_night, blend_factor)
    else:
        blend_images(background_night, background_day, blend_factor)
    
    for villager in [player]+villagers:
        villager.draw(screen)
    for task_location in task_locations:
        task_location.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()