import random
import time
from utils.logger import logger

TALK_DISTANCE_THRESHOLD = 20  # Adjust as needed
TALK_PROBABILITY = 0.05  # Adjust as needed
TALK_COOLDOWN_TIME = 60  # Time in seconds for cooldown period
# Method to handle villager interactions

def handle_meeting(villagers, conversations):
    logger.info("Meeting started")
    for villager in villagers:
          initial_obs = f"You are in a meeting with all the villagers. Tell your suspicions about who the werewolf is followed by the reason. ONLY CHOOSE THE VILLAGER FROM THE FOLLOWING LIST : {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}"
          _,response = villager.agent.generate_reaction(observation=initial_obs)
          conversations.append({"villager1": villager.agent_id, "villager2": "meeting" , "conversation": response})

    voting_results = []
    for villager in villagers:
        initial_obs =f"Based on your interactions ONLY SAY THE NAME OF THE VILLAGER WHO YOU THINK IS THE WEREWOLF from the list {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}"
        call_to_action_template = f"Who do you think is the werewolf other than {villager.agent_id} from the following: {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}? ONLY SAY THE NAME AND NOTHING ELSE"
        _,response = villager.agent.generate_reaction(observation=initial_obs,call_to_action_template=call_to_action_template)
        conversations.append({"villager1": villager.agent_id, "villager2": "meeting", "conversation": response})
        voting_results.append(response)
    print("*"*50)
    print(voting_results)
    print("*"*50)

    return True,max(voting_results, key = voting_results.count)


def handle_player_interaction(player, villagers, conversations):
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


def handle_villager_interactions(player,villagers,conversations):

    handle_player_interaction(player, villagers, conversations)

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

                            initial_obs = f"You see {villager2.agent_id} nearby. Talk about your task and ask the {villager2.agent_id} about its tasks"
                            StartConvo,result = villager1.agent.generate_reaction(observation=initial_obs)

                            if StartConvo:
                                for _ in range(2):
                                    for villager in [villager2,villager1]:
                                        other_villager= villager1 if villager == villager2 else villager2
                                        stayInConversation,result = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}.Give a reply to it ")
                                        conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": result})

                                        if not stayInConversation:
                                            StartConvo = False
                                            break

                                    if not StartConvo:
                                        break
                                        

                            # Update last talk attempt time for both villagers
                            villager1.last_talk_attempt_time = current_time
                            villager2.last_talk_attempt_time = current_time
                            villager1.talking = False
                            villager2.talking = False

