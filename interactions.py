import random

def villager_interactions(villagers):
    for i in range(len(villagers)):
        for j in range(i + 1, len(villagers)):
            if random.random() < 0.1:  # 10% chance of interaction
                villagers[i].interact(villagers[j])
