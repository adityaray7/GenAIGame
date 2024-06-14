import random
import time
from utils.logger import logger
from villager import Villager, Werewolf, Player

TALK_DISTANCE_THRESHOLD = 20  # Adjust as needed
TALK_PROBABILITY = 1 # Adjust as needed
TALK_COOLDOWN_TIME = 60  # Time in seconds for cooldown period
# Method to handle villager interactions

def handle_meeting(villagers, conversations,villager_remove):
    logger.info("Meeting started")
    for villager in villagers:
          initial_obs = f"You are in a meeting with all the villagers. Tell your suspicions about who the werewolf is followed by the reason. If you have no logical reason to suspect someone then don't make up facts. ONLY CHOOSE THE VILLAGER FROM THE FOLLOWING LIST : {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}"
          _,response = villager.agent.generate_reaction(observation=initial_obs)
          conversations.append({"villager1": villager.agent_id, "villager2": "meeting" , "conversation": response})

    voting_results = []
    for villager in villagers:
        initial_obs =f"Based on your interactions ONLY SAY THE NAME OF THE VILLAGER WHO YOU THINK IS THE WEREWOLF from the list {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}"
        call_to_action_template = f"Who do you think is the werewolf other than {villager.agent_id} from the following: {','.join([v.agent_id for v in villagers if v.agent_id != villager.agent_id])}? ONLY SAY THE NAME AND NOTHING ELSE"
        _,response = villager.agent.generate_reaction(observation=initial_obs,call_to_action_template=call_to_action_template)
        conversations.append({"villager1": villager.agent_id, "villager2": "meeting", "conversation": response})
        voting_results.append(response)
    
    villager_remove = max(voting_results, key = voting_results.count)

    if voting_results[villager_remove] < len(villagers)/2:
        villager_remove = None

    return True,villager_remove


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
                            
                            if isinstance(villager1, Werewolf):
                                # print("KILL")
                                initial_obs = f"You see {villager2.agent_id} nearby."
                                call_to_action_template = (
                                        f"How should {villager1.agent_id} the werewolf who kills {villager_list} react to the observation, and if so,"
                                        + " what would be an appropriate reaction? Respond in one line."
                                        + f"\nIf the action is to kill the {villager2.agent_id}, write:"
                                        + f'\nKILL: {villager2.agent_id} has been eliminated by {villager1.agent_id}'
                                        + '\notherwise, if the action is to engage in dialogue, write:'
                                        + '\nSAY: "what to say"'
                                        + "\notherwise if the action to react, write:"
                                        + "\nREACT: {agent_name}'s reaction (if anything)."
                                        + "\nEither do nothing, kill a villager, react, or say something but not both.\n\n"
                                    )
                                StartConvo,result = villager1.agent.generate_reaction(observation=initial_obs, call_to_action_template=call_to_action_template, villager=villager2.agent_id)
                                if "killed" in result:
                                    villagers.remove(villager2)
                                    Villager.killed_villagers.append(villager2)
                                    villager2.alive = False
                                conversations.append({"villager1": villager1.agent_id, "villager2": villager2.agent_id, "conversation": result})
                            else:
                                initial_obs = f"You see {villager2.agent_id} nearby. Talk about your task and ask the {villager2.agent_id} about its tasks"
                                StartConvo,result = villager1.agent.generate_reaction(observation=initial_obs)
                                conversations.append({"villager1": villager1.agent_id, "villager2": villager2.agent_id, "conversation": result})

                            if StartConvo:
                                for _ in range(2):
                                    for villager in [villager2,villager1]:
                                        other_villager = villager1 if villager == villager2 else villager2
                                        if isinstance(villager, Werewolf):
                                            call_to_action_template = (
                                                f"How should {villager.agent_id} the werewolf who kills {villager_list} react to the observation, and if so,"
                                                + " what would be an appropriate reaction? Respond in one line."
                                                + f"\nIf the action is to kill the {other_villager.agent_id}, write:"
                                                + f'\nKILL: {other_villager.agent_id} has been eliminated by {villager.agent_id}'
                                                + "Otherwise to end the conversation, write:"
                                                + '\nGOODBYE: "what to say". Otherwise to continue the conversation,'
                                                + '\nwrite: SAY: "what to say next"\n\n'
                                                )
                                            stayInConversation,result = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}.Give a reply to it ", call_to_action_template=call_to_action_template, villager=other_villager.agent_id)
                                            if "killed" in result:
                                                villagers.remove(other_villager)
                                                Villager.killed_villagers.append(other_villager)
                                                other_villager.alive = False
                                            conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": result})
                                        else:
                                            stayInConversation,result = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}. Write a logical and suitable reply. Only write the reply and nothing else")
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

