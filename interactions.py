'''
handle_villager_interactions
|
|-- handle_player_interaction
|
|-- handle_dead_villager_interaction
|   |
|   |-- get_nearest_task_location
|
|-- handle_villager_location_interactions
    |
    |-- get_nearest_task_location

handle_meeting
|
|-- get_nearest_task_location

get_nearest_task_location

'''

'''
handle_villager_interactions
|
|-- handle_player_interaction
|
|-- handle_dead_villager_interaction
|   |
|   |-- get_nearest_task_location
|
|-- handle_villager_location_interactions
    |
    |-- get_nearest_task_location

handle_meeting
|
|-- get_nearest_task_location

get_nearest_task_location

'''

import random
import time
from utils.logger import logger
from villager import Villager, Werewolf, Player
from task_manager import TaskManager

TALK_DISTANCE_THRESHOLD = 30  # Adjust as needed
TALK_PROBABILITY = 1  # Adjust as needed
TALK_COOLDOWN_TIME = 60  # Time in seconds for cooldown period

def get_nearest_task_location(villager):
    """
    Calculate the nearest task location for a given villager.

    Args:
        villager (Villager): The villager object.

    Returns:
        TaskLocation: The nearest task location to the villager.
    """
    task_manager = TaskManager()
    task_locations = task_manager.initialize_task_locations()
    min_distance = float('inf')
    nearest_location = None 
    for task_location in task_locations:
        distance = ((task_location.x - villager.x) ** 2 + (task_location.y - villager.y) ** 2) ** 0.5
        min_distance, nearest_location = (distance, task_location) if distance < min_distance else (min_distance, nearest_location)
    return nearest_location

def handle_meeting(villagers, conversations, villager_remove):
    """
    Handle the meeting where villagers discuss and vote on who they suspect is the werewolf.

    Args:
        villagers (list): List of living villagers.
        conversations (list): List to store conversations.
        villager_remove (str): Villager ID to be removed based on voting results.

    Returns:
        tuple: A tuple indicating whether the meeting was handled and the ID of the villager to remove.
    """
    logger.info("Meeting started")
    dead_villager_locations = [get_nearest_task_location(dead_villager).task for dead_villager in Villager.killed_villagers]
    voting_results = []
    villager_remove = None
    for villager in villagers:
        initial_obs = f"You are in a meeting with all the villagers. Tell your suspicions about who the werewolf is followed by the reason. If you have no logical reason to suspect someone then don't make up facts. ONLY CHOOSE THE VILLAGER FROM THE FOLLOWING LIST : {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}\n Last day the villager eliminated was {Villager.killed_villagers[-1].agent_id if Villager.killed_villagers else 'None' + ' near ' + dead_villager_locations[-1] if Villager.killed_villagers else 'None'}"
        call_to_action_template = (
            "What would {agent_name} say?\n"
            "Respond in the format 'I suspect: NAME. REASON'\n\n"
        )
        response = ""
        try:
            _, response = villager.agent.generate_reaction(observation=initial_obs, call_to_action_template=call_to_action_template)
            logger.info(f"{villager.agent_id}: {response}")
            response_lines = response.strip().split('.')
            for line in response_lines:
                if line.startswith("I suspect"):
                    agent_name = line.split(":")[1].strip()
                    voting_results.append(f"{agent_name}")
                    break
        except Exception as e:
            logger.error(f"Error parsing response from {villager.agent_id}: {e}")

        conversations.append({"villager1": villager.agent_id, "villager2": "meeting", "conversation": response})
    
    logger.info(f"Voting results: {voting_results}")

    if voting_results:
        villager_remove = max(voting_results, key=voting_results.count)

        count = 0
        for i in range(len(voting_results)):
            if voting_results[i] == villager_remove:
                count += 1

        if count <= len(villagers) / 2 - 1:
            villager_remove = None
    return True, villager_remove

def handle_player_interaction(player, villagers, conversations):
    """
    Handle interactions between the player and villagers.

    Args:
        player (Player): The player object.
        villagers (list): List of living villagers.
        conversations (list): List to store conversations.
    """
    """
    Handle interactions between the player and villagers.

    Args:
        player (Player): The player object.
        villagers (list): List of living villagers.
        conversations (list): List to store conversations.
    """
    current_time = time.time()
    for villager in villagers:
        if player != villager:
            if player.talking or villager.talking:
                continue
            distance = ((player.x - villager.x) ** 2 + (player.y - villager.y) ** 2) ** 0.5
            if distance < TALK_DISTANCE_THRESHOLD and random.random() < TALK_PROBABILITY and current_time - player.last_talk_attempt_time >= TALK_COOLDOWN_TIME:
                player.talking = True
                villager.talking = True

                for _ in range(2):
                    # Player initiates the conversation
                    player_input = input(f"Player: ")

                    # Villager responds using LLM
                    _, response = villager.agent.generate_reaction(observation=player_input)
                    print(f"{response}")

                    # Save conversation to the list
                    conversations.append({"villager1": "Player", "villager2": villager.agent_id, "conversation": player_input})
                    conversations.append({"villager1": villager.agent_id, "villager2": "Player", "conversation": response})

                # Update last talk attempt time for both player and villager
                player.last_talk_attempt_time = current_time
                villager.last_talk_attempt_time = current_time
                player.talking = False
                villager.talking = False

def handle_dead_villager_interaction(dead_villagers, villagers, conversations):
    """
    Handle interactions when a living villager encounters a dead villager.

    Args:
        dead_villagers (list): List of dead villagers.
        villagers (list): List of living villagers.
        conversations (list): List to store conversations.
    """
    for dead_villager in dead_villagers:
        for villager in villagers:
            if time.time() > villager.observation_countdown:
                distance = ((dead_villager.x - villager.x) ** 2 + (dead_villager.y - villager.y) ** 2) ** 0.5

                if distance < 5 * TALK_DISTANCE_THRESHOLD:
                    villager.observation_countdown = time.time() + 10
                    nearest_task_location = get_nearest_task_location(dead_villager)
                    someone_else = False
                    distance_dict = {}

                    for other_villager in villagers:
                        if other_villager.agent_id != villager.agent_id:
                            d = ((dead_villager.x - other_villager.x) ** 2 + (dead_villager.y - other_villager.y) ** 2) ** 0.5
                            if d < TALK_DISTANCE_THRESHOLD:
                                distance_dict[other_villager.agent_id] = d

                    if len(distance_dict.keys()) > 0:
                        someone_else = min(distance_dict, key=distance_dict.get)
                        someone_else = [villager for villager in villagers if villager.agent_id == someone_else][0]

                        logger.info(f"{villager.agent_id} sees dead villager {dead_villager.agent_id} near {nearest_task_location.task}.")
                        logger.info(f"{villager.agent_id} also sees {someone_else.agent_id} near the dead villager in {nearest_task_location.task}. Suspicion arises.")

                        villager.agent.memory.add_memory(f"You see {dead_villager.agent_id} dead near {someone_else.agent_id} in {nearest_task_location.task}. You suspect {someone_else.agent_id} is the werewolf.", agent_name=villager.agent_id)
                    else:
                        logger.info(f"{villager.agent_id} sees dead villager {dead_villager.agent_id} near {nearest_task_location.task}.")
                        villager.agent.memory.add_memory(f"You see {dead_villager.agent_id} dead near {nearest_task_location.task}.", agent_name=villager.agent_id)

def handle_villager_location_interactions(villagers):
    """
    Handle interactions based on the location of villagers.

    Args:
        villagers (list): List of living villagers.
    """
    for villager1 in villagers:
        for villager2 in villagers:
            if villager1 != villager2:
                distance = ((villager1.x - villager2.x) ** 2 + (villager1.y - villager2.y) ** 2) ** 0.5
                if distance < 5 * TALK_DISTANCE_THRESHOLD and time.time() > villager1.location_observation_countdown:
                    villager1.location_observation_countdown = time.time() + 10
                    nearest_task_location = get_nearest_task_location(villager2)
                    if nearest_task_location is not None:
                        logger.info(f"{villager1.agent_id} sees {villager2.agent_id} near {nearest_task_location.task}")
                        villager1.agent.memory.add_memory(f"You see {villager2.agent_id} near {nearest_task_location.task}", agent_name=villager1.agent_id)

def handle_villager_interactions(player, villagers, dead_villagers, conversations):
    """
    Handle all interactions involving villagers, including with the player, dead villagers, and other living villagers.

    Args:
        player (Player): The player object.
        villagers (list): List of living villagers.
        dead_villagers (list): List of dead villagers.
        conversations (list): List to store conversations.
    """
    handle_player_interaction(player, villagers, conversations)
    handle_dead_villager_interaction(dead_villagers, villagers, conversations)
    handle_villager_location_interactions(villagers)

    villager_list = ",".join([villager.agent_id for villager in villagers])
    current_time = time.time()
    for villager1 in villagers:
        for villager2 in villagers:
            if villager1 != villager2:
                if villager1.talking or villager2.talking:
                    continue
                distance = ((villager1.x - villager2.x) ** 2 + (villager1.y - villager2.y) ** 2) ** 0.5
                
                if distance < TALK_DISTANCE_THRESHOLD and random.random() < TALK_PROBABILITY and current_time - villager1.last_talk_attempt_time >= TALK_COOLDOWN_TIME:
                    villager1.talking = True
                    villager2.talking = True

                    StartConvo = False
                    stayInConversation = False
                            
                    if isinstance(villager1, Werewolf) and not isinstance(villager2, Werewolf):
                        initial_obs = f"You see {villager2.agent_id} nearby."
                        call_to_action_template = (
                                f"Should {villager1.agent_id}, the werewolf who eliminates {villager_list},"
                                + "react to the observation? And if so,"
                                + " what would be an appropriate reaction? Respond in one line."
                                + f"\nIf the action is to eliminate the {villager2.agent_id}, write:"
                                + f'\nELIMINATE: {villager2.agent_id} has been eliminated by {villager1.agent_id}'
                                + '\notherwise, if the action is to engage in dialogue, write:'
                                + '\nSAY: {agent_name}: ...'
                                + "\notherwise if the action to react, write:"
                                + "\nREACT: {agent_name}'s reaction (if anything)."
                                + "\nEither do nothing, eliminate a villager, react, or say something but not both.\n\n"
                            )
                        try:
                            StartConvo, result = villager1.agent.generate_reaction(observation=initial_obs, call_to_action_template=call_to_action_template, villager=villager2.agent_id)
                            if "eliminated" in result and time.time() > villager1.kill_cooldown:
                                villager1.kill_cooldown = time.time() + 30
                                villagers.remove(villager2)
                                Villager.killed_villagers.append(villager2)
                                dead_villagers.append(villager2)
                                villager2.alive = False
                                conversations.append({"villager1": villager1.agent_id, "villager2": villager2.agent_id, "conversation": result})
                        except Exception as e:
                            logger.error(f" {e}")
     
                    else:
                        try:
                            initial_obs = f"You see {villager2.agent_id} nearby. Talk about your task and ask the {villager2.agent_id} about its tasks"
                            StartConvo, result = villager1.agent.generate_reaction(observation=initial_obs)
                            conversations.append({"villager1": villager1.agent_id, "villager2": villager2.agent_id, "conversation": result})
                        except Exception as e:
                            logger.error(f"{e}")
     
                    if StartConvo:
                        for _ in range(2):
                            for villager in [villager2, villager1]:
                                other_villager = villager1 if villager == villager2 else villager2
                                if isinstance(villager, Werewolf) and not isinstance(other_villager, Werewolf):
                                    call_to_action_template = (
                                        f"How should {villager.agent_id} the werewolf who eliminates {villager_list} react to the observation, and if so,"
                                        + " what would be an appropriate reaction? Respond in one line."
                                        + f"\nIf the action is to eliminate the {other_villager.agent_id}, write:"
                                        + f'\nELIMINATE: {other_villager.agent_id} has been eliminated by {villager.agent_id}'
                                        + "Otherwise to end the conversation, write:"
                                        + '\nGOODBYE: "goodbye". Otherwise to continue the conversation,'
                                        + '\nwrite: SAY: {agent_name}: ...\n\n'
                                    )
                                    try:
                                        stayInConversation, result = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}. Give a reply to it ", call_to_action_template=call_to_action_template, villager=other_villager.agent_id)
                                        if "eliminated" in result and time.time() > villager.kill_cooldown:
                                            villagers.remove(other_villager)
                                            villager.kill_cooldown = time.time() + 30
                                            Villager.killed_villagers.append(other_villager)
                                            other_villager.alive = False
                                            conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": result})
                                        elif "eliminated" not in result:
                                            conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": result})
                                    except Exception as e:
                                        logger.error(f"{e}")
                                else:
                                    try:
                                        stayInConversation, result = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}. Write a logical and suitable reply. Only write the reply and nothing else")
                                        conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": result})
                                    except Exception as e:
                                        logger.error(f"{e}")
                                if not stayInConversation:
                                    StartConvo = False
                                    break

                            if not StartConvo:
                                break

                    villager1.last_talk_attempt_time = current_time
                    villager2.last_talk_attempt_time = current_time
                    villager1.talking = False
                    villager2.talking = False

