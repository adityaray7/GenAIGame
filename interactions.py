import random
import time

TALK_DISTANCE_THRESHOLD = 50  # Adjust as needed
TALK_PROBABILITY = 0.05  # Adjust as needed
TALK_COOLDOWN_TIME = 60  # Time in seconds for cooldown period
# Method to handle villager interactions


def handle_villager_interactions(villagers,conversations):
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
                                        stayInConversation,response = villager.agent.generate_dialogue_response(observation=f"{other_villager.agent_id} says {result}.Give a reply to it ")
                                        conversations.append({"villager1": villager.agent_id, "villager2": other_villager.agent_id, "conversation": response})

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

