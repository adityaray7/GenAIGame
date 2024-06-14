import pygame
import time
from utils.logger import logger
import random
from utils.agent import Agent
from langchain_core.language_models import BaseLanguageModel
from utils.agentmemory import AgentMemory
from dotenv import load_dotenv
import os
load_dotenv()

ELIMINATION_DISTANCE = 10
class Villager:
    killed_villagers = []
    def __init__(self, name, x, y, background_texts, llm : BaseLanguageModel, memory : AgentMemory,occupation="",meeting_location = (0,0),paths=[]):
        self.agent_id = name
        self.x = x
        self.y = y
        self.meeting_location = meeting_location
        self.background_texts = background_texts
        self.agent=Agent(name=name,status=occupation,memory=memory,llm=llm,description=background_texts)
        self.current_task = None
        self.task_location = None
        self.task_start_time = None
        self.task_end_time = 111717403133    
        self.task_doing = False
        self.time_to_complete_task = None
        self.last_talk_attempt_time = 0
        self.talking = False
        self.paths = paths
        self.font = pygame.font.SysFont(None, 24)
        self.alive = True

    def assign_task(self, task, location, time_to_complete_task):
        if self.alive == False:
            return
        self.current_task = task
        self.task_location = (location.x, location.y)
        self.time_to_complete_task = time_to_complete_task / float(os.getenv("SPEED"))
        self.task_doing = False
        self.task_start_time = None
        self.task_end_time = 111717403133

    # Returns True if the current time exceeds the end time of the task and False otherwise
    def task_complete(self):
        if self.alive == False:
            return
        if self.current_task is None:
            return False  # No task assigned
        else:
            # Check if the current time exceeds the end time of the task
            return time.time() >= self.task_end_time

    # Records the start and end time of the task and sets the task_doing flag to True
    def start_task(self):
        if self.alive == False:
            return
        # Record the start and end time of the task
        if not self.task_doing:
            logger.info(f"{self.agent_id} has started to do the task '{self.current_task}'!")
            self.task_doing = True
            self.task_start_time = time.time()
            self.task_end_time = self.task_start_time + self.time_to_complete_task

    def update(self):
        if self.alive == False:
            return
        
        if self.talking:
            return

        if self.task_doing:
            # Check if the task is complete
            if self.task_complete():
                logger.info(f"{self.agent_id} has completed the task '{self.current_task}'!")
                self.current_task = None
                self.time_to_complete_task = None
                self.task_doing = False
        else:
            if self.current_task is not None:
                # dx, dy = self.task_location[0] - self.x, self.task_location[1] - self.y
                # dist = (dx**2 + dy**2)**0.5
                # if dist > 1:
                #     self.x += dx / dist
                #     self.y += dy / dist
                # else:
                #     self.start_task()
            
            # Possible directions to move: up, down, left, right, and diagonals
                directions = [
                (0, -1), (0, 1), (-1, 0), (1, 0),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
                ]
                current_distance = self.distance_to_target(self.x, self.y)
                moved = False

                for direction in directions:
                    next_x = self.x + direction[0]
                    next_y = self.y + direction[1]
                    # print(self.agent_id)
                    # print(self.is_on_path(next_x, next_y, self.paths) , self.distance_to_target(next_x, next_y) , current_distance)

                    if self.distance_to_target(next_x, next_y) < current_distance:
                        self.x = next_x
                        self.y = next_y
                        moved = True
                        break

                if not moved:
                    # Move to the left if no valid move was found
                    next_x = self.x+ 1
                    next_y = self.y
                    if self.is_on_path(next_x, next_y, self.paths):
                        self.x = next_x
                        self.y = next_y

                if current_distance <= 1:
                    self.start_task()

    def is_on_path(self, x, y, paths):
            for path in paths:
                if path.rect.collidepoint(x, y):
                    return True
            return False
    
    def distance_to_target(self, x, y):
        dx = self.task_location[0] - x
        dy = self.task_location[1] - y
        return (dx ** 2 + dy ** 2) ** 0.5

    def interrupt_task(self):
        self.current_task = None
        self.task_doing = False
        self.last_talk_attempt_time = time.time()

    def draw(self, screen):
        color = (0, 0, 0) if self.task_doing else (255, 0, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)
        agent_id_text = self.font.render(self.agent_id, True, (0, 0, 0))
        screen.blit(agent_id_text, (self.x -25, self.y-40))
        if self.current_task:
            task_text = self.font.render(self.current_task, True, (0, 0, 0))
            screen.blit(task_text, (self.x + 10, self.y - 20))  # Display the task text above the villager
        vil_image = pygame.image.load(f'images/{self.agent_id.lower()}.png')
        vil_image = pygame.transform.scale(vil_image, (60, 60))
        if not self.alive:
            vil_image = pygame.transform.rotate(vil_image, 180)
        screen.blit(vil_image, (self.x-25, self.y-25))
            
    def get_eliminated(self):
        logger.info(f"{self.agent_id} has been eliminated!")
        self.alive = False

class Werewolf(Villager):
    def __init__(self, agent_id, x, y, background_texts, llm : BaseLanguageModel, memory : AgentMemory,occupation="",meeting_location = (0,0)):
        super().__init__(agent_id, x, y, background_texts, llm, memory, occupation, meeting_location)
        print(self.agent_id)
        self.is_werewolf = True

    def update(self):
        if self.talking:
            return

        if self.task_doing:
            if self.task_complete():
                logger.info(f"{self.agent_id} (Werewolf) sabotaged the task '{self.current_task}'!")
                self.current_task = None
                self.time_to_complete_task = None
                self.task_doing = False
                self.kill_cooldown = 0
        else:
            if self.current_task is not None:
                # dx, dy = self.task_location[0] - self.x, self.task_location[1] - self.y
                # dist = (dx**2 + dy**2)**0.5
                # if dist > 1:
                #     self.x += dx / dist
                #     self.y += dy / dist
                # else:
                #     self.start_task()
            
            # Possible directions to move: up, down, left, right, and diagonals
                directions = [
                (0, -1), (0, 1), (-1, 0), (1, 0),
                (-1, -1), (-1, 1), (1, -1), (1, 1)
                ]
                current_distance = self.distance_to_target(self.x, self.y)
                moved = False

                for direction in directions:
                    next_x = self.x + direction[0]
                    next_y = self.y + direction[1]
                    # print(self.agent_id)
                    # print(self.is_on_path(next_x, next_y, self.paths) , self.distance_to_target(next_x, next_y) , current_distance)

                    if self.distance_to_target(next_x, next_y) < current_distance:
                        self.x = next_x
                        self.y = next_y
                        moved = True
                        break

                if not moved:
                    # Move to the left if no valid move was found
                    next_x = self.x+ 1
                    next_y = self.y
                    if self.is_on_path(next_x, next_y, self.paths):
                        self.x = next_x
                        self.y = next_y

                if current_distance <= 1:
                    self.start_task()

    def eliminate(self, villager):
        if self.alive == False:
            return
        logger.info(f"{self.agent_id} has eliminated {villager.agent_id}!")

        dist = ((self.x - villager.x)**2 + (self.y - villager.y)**2)**0.5

        if dist < ELIMINATION_DISTANCE and time.time()>self.kill_cooldown:
            villager.get_eliminated()
            self.kill_cooldown = time.time() + 30
    

class Player(Villager):  # Inherits from the Villager class

    def __init__(self, name, x, y, background_texts, llm: BaseLanguageModel, memory: AgentMemory, occupation="", meeting_location=(0, 0),paths=[]):
        super().__init__(name, x, y, background_texts, llm, memory, occupation, meeting_location,paths=paths)
        self.speed = 1

    def handle_input(self):
        if self.alive == False:
            return
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed
        self.x += dx
        self.y += dy


    def update(self):
        self.handle_input()  # Handle player input
        # Call the parent class update method to handle tasks
        super().update()

    def draw(self, screen):
        color = (0, 255, 0)  # Green color for the player
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)
        agent_id_text = self.font.render(self.agent_id, True, (0, 0, 0))
        screen.blit(agent_id_text, (self.x + 10, self.y))
        if self.current_task:
            task_text = self.font.render(self.current_task, True, (0, 0, 0))
            screen.blit(task_text, (self.x + 10, self.y - 20))  # Display the task text above the player
        vil_image = pygame.image.load('images/vil.png')  # Assuming there's an image for the player
        vil_image = pygame.transform.scale(vil_image, (75, 75))
        screen.blit(vil_image, (self.x, self.y))  # Render the player image on the screen

