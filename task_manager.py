from task_locations import TaskLocation
from gpt_query import get_query

def initialize_task_locations():
    task_locations = [
        TaskLocation(1000, 300, "Gather food",5),
        TaskLocation(200, 200, "Build a house",10),
        TaskLocation(600, 600, "Collect wood",8),
        TaskLocation(80, 600, "Fetch water",10),
        TaskLocation(1000, 600, "Guard the village",25),
        TaskLocation(200, 500, "Cook food",10),
        TaskLocation(300, 100, "Hunt for animals",15),
        TaskLocation(600, 400, "Scout the area",10),
        TaskLocation(350, 350, "Heal the injured",12),
        TaskLocation(700, 200, "Teach children",10)
    ]
    return task_locations

def assign_tasks_to_villagers_from_llm(villagers, task_locations):
    for villager in villagers:
        query = f"What should be the next task for {villager.agent_id}? Expecting the response to be in the format Task: <task_name>,only assign one task from the following:{[loc.task for loc in task_locations]}"

        context = " ".join(villager.background_texts)
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": query}
        ]
        response = get_query(messages)

        try:
            task_name = response.strip().split(':')[1].strip()
            task_location = next((loc for loc in task_locations if loc.task == task_name), None)
            if task_location:
                task_time = task_location.task_period  # Time required for the task
                villager.assign_task(task_name, task_location,task_time)
                print(f"Assigned task '{task_name}' to  {villager.agent_id} at location ({task_location.x}, {task_location.y})")
            else:
                print(f"Task '{task_name}' not found in available task locations.")
        except IndexError:
            print(f"Unexpected response format: {response}")
            default_task_location = task_locations[0]
            default_task_time = default_task_location.task_period
            villager.assign_task(default_task_location.task, default_task_location,default_task_time)

        


def assign_next_task(villager, task_locations,previous_task):
    query = f"What should be the next task for {villager.agent_id}?  Expecting the response to be in the format Task: <task_name>,only assign one task from the following:{[loc.task for loc in task_locations]} other than {previous_task}"
    context = " ".join(villager.background_texts)
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": query}
    ]
    response = get_query(messages)

    try:
        task_name = response.strip().split(':')[1].strip()
        task_location = next((loc for loc in task_locations if loc.task == task_name), None)
        task_time = task_location.task_period  # Time required for the task
        if task_location:
            villager.assign_task(task_name, task_location,task_time)
            print(f"Assigned task '{task_name}' to {villager.agent_id} at location ({task_location.x}, {task_location.y})\n")
        else:
            print(f"Task '{task_name}' not found in available task locations.")
    except IndexError:
        print(f"Unexpected response format: {response}\n")
        default_task_location = task_locations[0]
        default_task_time = default_task_location.task_period

        villager.assign_task(default_task_location.task, default_task_location,default_task_time)


    return task_name, task_location
