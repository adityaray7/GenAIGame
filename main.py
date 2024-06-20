from utils.logger import logger
import pygame
import random
from task_manager import TaskManager, assign_next_task, assign_first_task
import json
import os
from dotenv import load_dotenv
from pygame import mixer
import time
import deepl
from interactions import handle_villager_interactions,handle_meeting
from threading import Thread
from utils.task_locations import Path
from utils.to_be_threaded_function import threaded_function
from client import send
import math
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain_mongodb import MongoDBAtlasVectorSearch
load_dotenv()
from utils.mongoClient import get_atlas_collection, get_atlas_collections
from colorama import Fore
from villager import Villager, Werewolf, Player
from utils.agentmemory import AgentMemory
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

llm = AzureChatOpenAI(
    azure_deployment="GPT35-turboA",
    api_version="2024-02-01",
    temperature=0
)

# Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
DAY_DURATION = 90  # 60 seconds for a full day cycle
NIGHT_DURATION = 90  # 60 seconds for a full night cycle
TRANSITION_DURATION = 10  # 10 seconds for a transition period
MORNING_MEETING_DURATION = 25

# Load background images
background_day = pygame.image.load("images/map3.png")
background_night = pygame.image.load("images/night3.png")
background_day = pygame.transform.scale(background_day, (SCREEN_WIDTH, SCREEN_HEIGHT))
background_night = pygame.transform.scale(background_night, (SCREEN_WIDTH, SCREEN_HEIGHT))


'''
Initialize the mixer
'''
mixer.init()
mixer.music.load('music/music.mp3')


'''Initialize the pygame'''
names=["Akio","Chiyo","Hana","Izumi","Kaio"]
werewolf_names=["Katsumi","Madara"]
convo_collection_names=["Akio_convo","Chiyo_convo","hana_convo","Izumi_convo","Kaio_convo"]
werewolf_convo_collection_names=["Katsumi_convo","Madara_convo"]


'''Initialize the mongo connection'''
ATLAS_CONNECTION_STRING=os.getenv("ATLAS_CONNECTION_STRING")
deepl_auth_key = os.getenv("DEEPL_AUTH_KEY")
mongo_connection_holder = {}
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

collection_names = names+werewolf_names+convo_collection_names+werewolf_convo_collection_names
collections_holder = {}

villager_mongo_connection = Thread(target=threaded_function, args=(collections_holder, get_atlas_collections, (db_name, collection_names)))
villager_mongo_connection.start()

# Mongo connection thread
mongo_connection_thread.join()
convo_connection_thread.join()
villager_mongo_connection.join()
atlas_collection = client_holder["result"]
convo_collection = convo_holder["result"]
villager_connections = collections_holder["result"]

villager_collections = {}

for i,name in enumerate(names+werewolf_names):
    villager_collections[name] = (villager_connections[i],villager_connections[len(names+werewolf_names)+i])

def create_new_memory_retriever(agent_name="Player"):
    """Create a new vector store retriever unique to the agent."""
    # Define your embedding model
    print("creating memory retriever for",agent_name)
    embeddings_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding3",
        api_version="2024-02-01"
    )
    if(agent_name=="Player"):
        agent_collection = atlas_collection
    else:    
        agent_collection = villager_collections[agent_name][0]
    vectorstore = MongoDBAtlasVectorSearch(agent_collection, embeddings_model)

    return TimeWeightedVectorStoreRetriever(
        vectorstore=vectorstore, other_score_keys=["importance"], k=15, decay_rate=0.005
    )

# Multithreading 
villagers_threaded = []


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()


'''
Initialize the backgrounds
'''
backgrounds = [
    ["I am Akio. I enjoy exploring the woods and gathering herbs. The forest is my sanctuary, where I feel most alive and connected to nature.",
    "I often cook meals for my fellow villagers. Using the herbs and plants I gather, I create nutritious and flavorful dishes that keep everyone in good health and spirits.",
    "My knowledge of the forest's flora allows me to prepare remedies for common ailments, ensuring our village remains healthy and strong.",
    "Keep an eye on other villagers while talking, and in the meeting, raise your suspicion on the werewolf"],

    ["I am Chiyo. I have a knack for construction and enjoy building structures. From homes to storage sheds, my craftsmanship ensures our village is well-built and resilient.",
    "I believe a sturdy village is key to our safety. By using strong materials and innovative designs, I create buildings that can withstand harsh weather and potential threats.",
    "I also lead repair and maintenance efforts, making sure that every structure stands the test of time and continues to serve our community.",
    "Keep an eye on other villagers while talking, and in the meeting, raise your suspicion on the werewolf"],

    ["I am Hana. I am always on high alert, watching over the village day and night. My keen eyes and sharp senses make me an excellent guardian.",
    "I take pride in keeping everyone safe from harm. Whether it's warding off wild animals or keeping an eye out for intruders, my vigilance ensures our village's security.",
    "I train younger villagers in self-defense and alertness, passing on my knowledge so that they too can contribute to the safety of our home.",
    "Keep an eye on other villagers while talking, and in the meeting, raise your suspicion on the werewolf"],

    ["I am Izumi. I have a deep connection with water, be it rivers, lakes, or the rain. My days are spent ensuring that our village has clean and ample water supply.",
    "Water management is crucial for our survival. By maintaining the irrigation systems and wells, I ensure that our crops are well-watered and our people have fresh water to drink.",
    "I also have a talent for fishing and often bring fresh fish to the village. My knowledge of aquatic life helps in providing another source of sustenance for everyone.",
    "Keep an eye on other villagers while talking, and in the meeting, raise your suspicion on the werewolf"],

    ["I am Kaio. The fields are my domain, and farming is my passion. I work tirelessly to cultivate crops that provide nourishment for our entire village.",
    "I believe in sustainable farming practices that keep our soil fertile and productive year after year. By rotating crops and using natural fertilizers, I ensure we have bountiful harvests.",
    "I also enjoy teaching others about agriculture, passing down techniques and knowledge that have been handed down through generations. Together, we keep our village thriving.",
    "Keep an eye on other villagers while talking, and in the meeting, raise your suspicion on the werewolf"]
]

werewolf_backgrounds = [
    ["I am Katsumi ","I am a werewolf and I am here to sabotage the tasks and eliminate villagers.","I DO NOT reveal my identity to anyone. DO NOT take the name of the werewolf in the meeting and blame others."],
    ["I am Uchiha Madara ","I am a werewolf and I am here to sabotage the tasks.","I DO NOT reveal my identity to anyone. DO NOT take the name of the werewolf in the meeting and blame others."]
]


'''
walkable paths
'''
paths = [
    # Pathways leading to the meeting point
    Path(SCREEN_WIDTH // 2 + 60, SCREEN_HEIGHT // 2 - 30, 800, 30),
    Path(0, SCREEN_HEIGHT // 2 - 30, 700, 30),
    Path(SCREEN_WIDTH // 2 - 30, 0, 30, 400),
    Path(SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT // 2 + 40, 30, 400),

    # Meeting point
    Path(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 100, 200, 60),
    Path(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 40, 200, 60),
    Path(SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2 - 60, 60, 150),
    Path(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 60, 60, 150),

    # Outer horizontal path
    Path(0, SCREEN_HEIGHT // 4 - 25, 1500, 30),
    Path(0, 3 * SCREEN_HEIGHT // 4, 1500, 30),

    # Inner vertical paths
    Path(SCREEN_WIDTH // 4 - 75, 0, 30, 900),
    Path(3 * SCREEN_WIDTH // 4 + 25, 0, 30, 900),

    # Outer vertical path
    Path(30, 0, 30, 900),
    Path(SCREEN_WIDTH - 60, 0, 30, 900)
]


'''
Initialize the villagers
'''
villagers = []
num_villagers = len(names)
num_werewolf = len(werewolf_names)
center_x = SCREEN_WIDTH//2
center_y = SCREEN_HEIGHT//2
radius = 65

angles = [i * (2 * math.pi / (num_villagers+num_werewolf) ) for i in range(num_villagers+num_werewolf)]
for i in range(len(backgrounds)):
    angle = angles[i]
    x = int(center_x + radius * math.cos(angle))
    y = int(center_y + radius * math.sin(angle))
    background_texts = backgrounds[i]
    ". ".join(a for a in background_texts)

    villager_memory = AgentMemory(llm=llm, memory_retriever=create_new_memory_retriever(names[i]))
    villager = Villager(names[i], x, y, background_texts=background_texts,llm=llm,memory=villager_memory,meeting_location=(x,y),paths=paths)
    villager.last_talk_attempt_time = 0  # Initialize last talk attempt time
    villagers.append(villager)
    j=i+1

for i in range(len(werewolf_backgrounds)):
    angle = angles[j]
    x = int(center_x + radius * math.cos(angle))
    y = int(center_y + radius * math.sin(angle))
    background_texts = werewolf_backgrounds[i]
    ". ".join(a for a in background_texts)
    werewolf_memory = AgentMemory(llm=llm, memory_retriever=create_new_memory_retriever(werewolf_names[i]))
    werewolf = Werewolf(werewolf_names[i], x, y, background_texts=background_texts,llm=llm,memory=werewolf_memory,meeting_location=(x,y))
    werewolf.last_talk_attempt_time = 0  # Initialize last talk attempt time
    villagers.append(werewolf)
    j+=1

'''
Initialize the player
'''
player_memory = AgentMemory(llm=llm, memory_retriever=create_new_memory_retriever())
player = Player("Player", SCREEN_WIDTH // 2+100, SCREEN_HEIGHT // 2 + 100, ["I am Aditya.I am the village head. I am just on a round to make sure everything is going good"], llm,memory = player_memory, meeting_location=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),paths=paths)


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

'''
Functions to save the conversations
'''

def save_game_state(villagers, filename="game_state.json"):
    with open(filename, 'w') as f:
        json.dump(villager_info(villagers), f, indent=4)

# Function to save conversations to MongoDB
def save_conversations_to_mongodb(conversations):
    if conversations:
        convo_collection.insert_many(conversations)
        if conversations[0]["villager1"] in villager_collections:
            villager_collections[conversations[0]["villager1"]][1].insert_many(conversations)
        
        logger.info(f"Saved {len(conversations)} conversations to MongoDB.")
        
    else:
        logger.info("No new conversations to save.")

# Function to save conversations to a JSON file
def save_conversations(conversations, filename="conversations.json"):
    with open(filename, 'w') as f:
        json.dump(conversations, f, indent=4)

'''
utility functions
'''

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

# Function to display text on the screen with a white background
def display_text(screen, text, duration, font_size=50):
    font = pygame.font.Font(None, font_size)
    rendered_text = font.render(text, True, (255, 0, 0))  # Red color text
    text_rect = rendered_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    background_rect = pygame.Rect(0, 0, text_rect.width + 20, text_rect.height + 20)
    background_rect.center = text_rect.center

    start_time = time.time()
    while time.time() - start_time < duration:
        screen.fill((255, 255, 255), background_rect)  # White background
        screen.blit(rendered_text, text_rect)
        pygame.display.flip()
        clock.tick(60)

# Initialize task locations
task_manager = TaskManager()
task_locations = task_manager.tasks
global meetCheck
meetCheck = False

'''
Game state functions
'''
# Function to send game state to the 
def send_game_state():
    global villagers
    global is_day,blend_factor
    global player_coordinates
    villagers_state = []
    num_villagers = len(villagers)
    for villager in villagers:
        villagers_state.append({
            "agent_id": villager.agent_id,
            "x": villager.x,
            "y": villager.y
        })
        
    villagers_state.append({
        "agent_id": "Player",
        "x": player_coordinates[0],
        "y": player_coordinates[1]
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
    result = None
    if conversations:
        isConvo=True
        translator = deepl.Translator(deepl_auth_key)
        print(conversations[0]['conversation'])
        split_text = conversations[0]['conversation'].split(':', 1)
        if len(split_text) > 1:
            conversation_text = split_text[1].strip()  # Remove leading/trailing whitespace
        else:
            conversation_text = split_text[0].strip() 
        result = translator.translate_text(conversation_text, target_lang="JA")
        print("Translated text: ", result.text)
          
      
    game_state = {
        "numVillagers": num_villagers,
        "villagers": villagers_state,
        "tasks": task_info, 
        "isDay": is_day,
        "blendFactor": blend_factor,
        "isConvo":isConvo,
        "conversations": conversations,
        "translatedText":result.text if result else "",
        "is_morning_meeting": meetCheck
    }

    # convert game_state to json
    game_state = json.dumps(game_state)
    send(game_state)


'''
Task assignment thread
'''
assign_first_task(villagers,task_locations,task_manager.completed_tasks(),task_manager.incomplete_tasks())
conversations = []  # List to store conversations

def assign_task_thread(villager, current_task=None):
    global task_locations
    if (villager.agent_id in villagers_threaded):
        return
    villagers_threaded.append(villager.agent_id)
    logger.info(f"{villagers_threaded} are the villagers currently getting assigned tasks")
    logger.debug(f"Assigning next task to {villager.agent_id}...")

    if isinstance(villager, Werewolf):
        task_name, task_location = assign_next_task(villager, task_manager.completed_tasks(), current_task)
        # print(villager.agent_id, task_name,  task_manager.completed_tasks())
    else:
        task_name, task_location = assign_next_task(villager, task_manager.incomplete_tasks(), current_task)
        # print(villager.agent_id, task_name,  task_manager.incomplete_tasks())
    task_time = task_location.task_period  # Time required for the task
    task_complete_function = task_location.complete
    task_sabotage_function = task_location.sabotage

    if isinstance(villager, Werewolf):
        villager.assign_task(task_name, task_location, task_time, task_sabotage_function)
    else:
        villager.assign_task(task_name, task_location, task_time, task_complete_function)
    logger.info(f"{villager.agent_id} is now assigned the task '{task_name}'... ({task_time} seconds)")
    villagers_threaded.remove(villager.agent_id)



'''
Morning meeting functions
'''
def morning_meeting(villagers,conversations,elapsed_time):
    global is_morning_meeting
    is_morning_meeting = True
    global reached
    reached = True
    temp = elapsed_time
    meeting_complete = False
    villager_remove = False
    for villager in villagers:
        villager.interrupt_task()
        dx, dy = villager.meeting_location[0] - villager.x, villager.meeting_location[1] - villager.y
        dist = (dx**2 + dy**2)**0.5
        if dist > 2:
            villager.x += 2*dx / dist
            villager.y += 2*dy / dist
            reached = False    
    if reached and elapsed_time>5:
        logger.info("All villagers have gathered for the morning meeting.")
        display_text(screen,"Meeting Going On......", 1)
        meeting_complete,villager_remove =handle_meeting(villagers, conversations,villager_remove)
        elapsed_time = temp
        return meeting_complete,elapsed_time + MORNING_MEETING_DURATION,villager_remove
    return meeting_complete,elapsed_time,villager_remove
    
def end_morning_meeting(villagers):
    global is_morning_meeting
    is_morning_meeting = False
    for villager in villagers:
        villager.talking = False    
    Villager.killed_villagers.clear()
    assign_first_task(villagers, task_locations,task_manager.completed_tasks(),task_manager.incomplete_tasks())


mixer.music.play(-1)

'''
MAIN GAME LOOP
'''
running = True
start_time = time.time()
is_day = True
blend_factor = 0
is_morning_meeting = False
meeting_complete = False
message = None
message_start_time = None
message_duration = 5
dead_villagers = []
player_coordinates = (player.x, player.y)

while running:

    send_game_state()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update()
    player_coordinates = (player.x, player.y)

    curr = time.time() + MORNING_MEETING_DURATION  #increased so that first meeting is skipped
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
                meetCheck=True
                logger.info("Starting morning meeting...")   
            meeting_complete,_,remove_villager = morning_meeting(villagers,conversations,elapsed_time)

            if remove_villager:
                logger.info(f"Eliminating {remove_villager} from the village...")
                for villager in villagers:
                    if villager.agent_id == remove_villager:
                        villagers.remove(villager)
                        message = f"{villager.agent_id} was kicked out"
                        message_start_time = time.time()
                        break


        elif elapsed_time > MORNING_MEETING_DURATION and meeting_complete and is_morning_meeting:
            logger.info("Ending morning meeting...")
            meetCheck=False
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
    
    Thread(target=handle_villager_interactions, args=(player,villagers,Villager.killed_villagers,conversations)).start()

    # Save game state periodically
    save_game_state(villagers)
    save_conversations(conversations)
    if conversations:
        print(Fore.RED + "\nconversations")
        for convo in conversations:
            print(Fore.RED+ convo['villager1'] + " to " +  convo['villager2'] + " : " + convo['conversation'].split(":")[-1])
        save_conversations_to_mongodb(conversations)
    conversations.clear()  # Clear the list after saving

    # Render game state
    if is_day:
        blend_images(background_day, background_night, blend_factor)
    else:
        blend_images(background_night, background_day, blend_factor)

    for villager in [player]+villagers+Villager.killed_villagers:
        villager.draw(screen)

    for task_location in task_locations:
        task_location.draw(screen)

     # Display message if there is one
    if message and time.time() - message_start_time < message_duration:
        display_text(screen, message, message_duration)

    else:
        # Check for win conditions
        if len([villager for villager in villagers if isinstance(villager, Villager)])<=2:
            message = "Werewolves won the game!"
            message_start_time = time.time()
            # Remove all villagers
            

        elif all(not isinstance(villager, Werewolf) for villager in villagers):
            message = "Townsfolk won the game!"
            message_start_time = time.time()

        elif task_manager.all_tasks_completed():
            message = "Townsfolk won the game!"
            message_start_time = time.time()

    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()