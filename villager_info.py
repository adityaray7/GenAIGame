import json

def read_game_state(filename="game_state.json"):
    with open(filename, 'r') as f:
        return json.load(f)

def print_villager_info(villagers_info):
    for info in villagers_info:
        print(f"Agent ID: {info['agent_id']}")
        print(f"Position: ({info['x']}, {info['y']})")
        print(f"Current Task: {info['current_task']}")
        print(f"Task Start Time: {info['task_start_time']}")
        print(f"Task End Time: {info['task_end_time']}")
        print(f"Task Doing: {info['task_doing']}")
        print(f"Talking: {info['talking']}")
        print("-" * 20)

if __name__ == "__main__":
    villagers_info = read_game_state()
    print_villager_info(villagers_info)
