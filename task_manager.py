from utils.task_locations import Task
from utils.logger import logger
import random
from villager import Werewolf

class TaskManager:
    def __init__(self) -> None:
        self.tasks = self.initialize_task_locations()

    def initialize_task_locations(self):
        return [
            Task(1100, 650, "Gather food",5),
            Task(1100, 200, "Build a house",10),
            Task(1400, 100, "Collect wood",8),
            Task(80, 700, "Fetch water",10),
            Task(900, 450, "Guard the village",15),
            Task(400, 650, "Cook food",10),
            Task(100, 100, "Hunt for animals",15),
            Task(600, 400, "Scout the area",10),
            Task(400, 400, "Heal the injured",12),
            Task(700, 200, "Teach children",10)
        ]

    def completed_tasks(self):
        return [task for task in self.tasks if task.completed]

    def incomplete_tasks(self):
        return [task for task in self.tasks if not task.completed]
    
    def all_tasks_completed(self):
        return all(task.completed for task in self.tasks)


def assign_first_task(villagers, task_locations,complete,incomplete):

    print(complete)
    print(incomplete)
    for i in range(len(villagers)):
        villager = villagers[i]

        if isinstance(villager,Werewolf):
            if complete:
                task = random.choice(complete)
                task_name = task.task
            else:
                task= random.choice(incomplete)
                task_name = task.task
            task_location = [loc for loc in task_locations if loc.task == task_name][0]
            task_time = task_location.task_period  # Time required for the task
            task_sabotage_function = task_location.sabotage
            villager.assign_task(task_name, task_location, task_time, task_sabotage_function)
            logger.debug(f"Sabotage task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})")

        else:
            task = random.choice(incomplete)
            task_name = task.task
            print([loc for loc in task_locations if loc.task == task_name])
            task_location = [loc for loc in task_locations if loc.task == task_name][0]
            task_time = task_location.task_period
            task_complete_function = task_location.complete
            villager.assign_task(task_name, task_location, task_time, task_complete_function)
            logger.debug(f"Assigned task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})")


def assign_next_task(villager, task_locations,previous_task):
    # task_location = random.choice(task_locations)
    # task_name = task_location.task
    # villager.assign_task(task_name, task_location, task_location.task_period, task_location.complete)
    # logger.debug(f"Assigned task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})")
    
    # return task_name, task_location
    if len(task_locations) == 0:
        tm = TaskManager()
        task_locations = tm.initialize_task_locations()

    try:
        _,response = villager.agent.generate_reaction(observation=f"only assign one task from the following:{[loc.task for loc in task_locations]} other than {previous_task}",call_to_action_template="What should be the next task for "+villager.agent_id+f"? Expecting the response to be in the format Task: <task_name>. Do not assign other than from the given list. only assign one task from the following:{[loc.task for loc in task_locations]} ")

        print(response)
        task_name = response.strip().split(':')[1].strip()
        task_location = [loc for loc in task_locations if loc.task == task_name][0]
        
        print("*"*50)
        print(task_name)

        task_time = task_location.task_period  # Time required for the task
        task_complete_function = task_location.complete
        # villager.assign_task(task_name, task_location,task_time, task_complete_function)
        logger.debug(f"Assigned task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})")

    except IndexError:
        logger.error(f"Unexpected response format: {response}\n")
        default_task_location = random.choice(task_locations)
        # default_task_time = default_task_location.task_period
        # task_complete_function = default_task_location.complete

        # villager.assign_task(default_task_location.task, default_task_location,default_task_time,task_complete_function )
        return default_task_location.task, default_task_location

    return task_name, task_location
