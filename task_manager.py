from utils.task_locations import TaskLocation
from utils.gpt_query import get_query
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import logger
import random

def initialize_task_locations():
    task_locations = [
        TaskLocation(1000, 300, "Gather food",5),
        TaskLocation(200, 200, "Build a house",10),
        TaskLocation(600, 600, "Collect wood",8),
        TaskLocation(80, 600, "Fetch water",10),
        TaskLocation(1000, 600, "Guard the village",15),
        TaskLocation(200, 500, "Cook food",10),
        TaskLocation(300, 100, "Hunt for animals",15),
        TaskLocation(600, 400, "Scout the area",10),
        TaskLocation(350, 350, "Heal the injured",12),
        TaskLocation(700, 200, "Teach children",10)
    ]
    return task_locations

def assign_tasks_to_villagers_from_llm(villagers, task_locations):
    
    for villager in villagers:
        _,response = villager.agent.generate_reaction(observation="only assign one task from the following:"+str([loc.task for loc in task_locations])+" other than None",call_to_action_template="What should be the first task for "+villager.agent_id+"? Expecting the response to be in the format Task: <task_name>")
        print(response)

        try:
            task_name = response.strip().split(':')[1].strip()
            task_location = next((loc for loc in task_locations if loc.task == task_name), None)
            if task_location:
                task_time = task_location.task_period  # Time required for the task
                villager.assign_task(task_name, task_location, task_time)
                logger.debug(f"Assigned task '{task_name}' to  {villager.agent_id} at location ({task_location.x}, {task_location.y})")
            else:
                logger.warning(f"Task '{task_name}' not found in available task locations.")
        except IndexError:
            logger.error(f"Unexpected response format: {response}")
            default_task_location = task_locations[0]
            default_task_time = default_task_location.task_period
            villager.assign_task(default_task_location.task, default_task_location, default_task_time)      


def assign_next_task(villager, task_locations,previous_task):
    query = f"What should be the next task for {villager.agent_id}?  Expecting the response to be in the format Task: <task_name>,only assign one task from the following:{[loc.task for loc in task_locations]} other than {previous_task}.Do not assign other than from the given list"
    
    _,response = villager.agent.generate_reaction(observation="only assign one task from the following:{[loc.task for loc in task_locations]} other than {previous_task}",call_to_action_template="What should be the next task for "+villager.agent_id+"? Expecting the response to be in the format Task: <task_name>. Do not assign other than from the given list")
    print(response)

    try:
        task_name = response.strip().split(':')[1].strip()
        task_location = random.choice([task for task in task_locations if task != previous_task])
        if task_location in task_locations:
            task_time = task_location.task_period  # Time required for the task
            villager.assign_task(task_name, task_location,task_time)
            logger.debug(f"Assigned task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})")
        else:
            default_task_location = next((loc for loc in task_locations), previous_task)
            default_task_name = default_task_location.task
            default_task_time = default_task_location.task_period
            villager.assign_task(default_task_name, default_task_location,default_task_time)
            logger.warning(f"Task '{task_name}' not found in available task locations.")

    except IndexError:
        logger.error(f"Unexpected response format: {response}\n")
        default_task_location = task_locations[0]
        default_task_time = default_task_location.task_period

        villager.assign_task(default_task_location.task, default_task_location,default_task_time)

    return task_name, task_location
