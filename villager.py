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

ELIMINATION_DISTANCE = 40
SPEED = 2

class Villager:
    """
    Represents a villager in the game.

    Attributes:
        killed_villagers (list): List to keep track of killed villagers.
        agent_id (str): The ID of the villager.
        x (int): X-coordinate of the villager's position.
        y (int): Y-coordinate of the villager's position.
        meeting_location (tuple): The meeting location coordinates.
        background_texts (str): Background information for the villager.
        agent (Agent): The agent representing the villager.
        current_task (str): The current task assigned to the villager.
        task_location (tuple): The location of the current task.
        task_complete_function (function): The function to call when the task is completed.
        task_start_time (float): The start time of the task.
        task_end_time (float): The end time of the task.
        task_doing (bool): Indicates if the villager is currently doing a task.
        time_to_complete_task (float): The time required to complete the task.
        last_talk_attempt_time (float): The last time the villager attempted to talk.
        talking (bool): Indicates if the villager is currently talking.
        paths (list): The paths the villager can move on.
        font (pygame.font.Font): The font used for rendering text.
        alive (bool): Indicates if the villager is alive.
        observation_countdown (float): Countdown timer for observations.
        location_observation_countdown (float): Countdown timer for location observations.
    """

    killed_villagers = []

    def __init__(self, name, x, y, background_texts, llm: BaseLanguageModel, memory: AgentMemory, occupation="", meeting_location=(0, 0), paths=[]):
        self.agent_id = name
        self.x = x
        self.y = y
        self.meeting_location = meeting_location
        self.background_texts = background_texts
        self.agent = Agent(name=name, status=occupation, memory=memory, llm=llm, description=background_texts)
        self.current_task = None
        self.task_location = None
        self.task_complete_function = None
        self.task_start_time = None
        self.task_end_time = 111717403133    
        self.task_doing = False
        self.time_to_complete_task = None
        self.last_talk_attempt_time = 0
        self.talking = False
        self.paths = paths
        self.font = pygame.font.SysFont(None, 24)
        self.alive = True
        self.observation_countdown = time.time()
        self.location_observation_countdown = time.time()

    def assign_task(self, task, location, time_to_complete_task, task_complete_function):
        """
        Assign a task to the villager.

        Parameters:
            task (str): The task to assign.
            location (tuple): The location of the task.
            time_to_complete_task (float): The time required to complete the task.
            task_complete_function (function): The function to call when the task is completed.
        """
        if not self.alive:
            print(f"{self.agent_id} is dead hence can't be assigned a task")
            return
        self.current_task = task
        self.task_complete_function = task_complete_function
        self.task_location = (location.x, location.y)
        self.time_to_complete_task = time_to_complete_task / float(os.getenv("SPEED"))
        self.task_doing = False
        self.task_start_time = None
        self.task_end_time = 111717403133

    def task_complete(self):
        """
        Check if the current task is complete.

        Returns:
            bool: True if the task is complete, False otherwise.
        """
        if not self.alive:
            return False
        return self.current_task is not None and time.time() >= self.task_end_time

    def start_task(self):
        """
        Start the current task.
        """
        if not self.alive:
            return
        if not self.task_doing:
            logger.info(f"{self.agent_id} has started to do the task '{self.current_task}'!")
            self.task_doing = True
            self.task_start_time = time.time()
            self.task_end_time = self.task_start_time + self.time_to_complete_task

    def update(self):
        """
        Update the villager's state.
        """
        if not self.alive or self.talking:
            return

        if self.task_doing:
            if self.task_complete():
                logger.info(f"{self.agent_id} has completed the task '{self.current_task}'!")
                self.task_complete_function()
                self.current_task = None
                self.time_to_complete_task = None
                self.task_doing = False
        else:
            if self.current_task is not None:
                directions = [
                    (0, -1), (0, 1), (-1, 0), (1, 0),
                    (-1, -1), (-1, 1), (1, -1), (1, 1)
                ]
                current_distance = self.distance_to_target(self.x, self.y)
                moved = False

                for direction in directions:
                    next_x = self.x + SPEED * direction[0]
                    next_y = self.y + SPEED * direction[1]

                    if self.distance_to_target(next_x, next_y) < current_distance:
                        self.x = next_x
                        self.y = next_y
                        moved = True
                        break

                if not moved:
                    next_x = self.x + SPEED
                    next_y = self.y
                    if self.is_on_path(next_x, next_y, self.paths):
                        self.x = next_x
                        self.y = next_y

                if current_distance <= 2:
                    self.start_task()

    def is_on_path(self, x, y, paths):
        """
        Check if the given coordinates are on a path.

        Parameters:
            x (int): X-coordinate to check.
            y (int): Y-coordinate to check.
            paths (list): List of paths.

        Returns:
            bool: True if the coordinates are on a path, False otherwise.
        """
        for path in paths:
            if path.rect.collidepoint(x, y):
                return True
        return False

    def distance_to_target(self, x, y):
        """
        Calculate the distance to the target task location.

        Parameters:
            x (int): X-coordinate of the current position.
            y (int): Y-coordinate of the current position.

        Returns:
            float: Distance to the target task location.
        """
        dx = self.task_location[0] - x
        dy = self.task_location[1] - y
        return (dx ** 2 + dy ** 2) ** 0.5

    def interrupt_task(self):
        """
        Interrupt the current task.
        """
        self.current_task = None
        self.task_doing = False
        self.last_talk_attempt_time = time.time()

    def draw(self, screen):
        """
        Draw the villager on the screen.

        Parameters:
            screen (pygame.Surface): The screen to draw on.
        """
        color = (0, 0, 0) if self.task_doing else (255, 0, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)
        agent_id_text = self.font.render(self.agent_id, True, (0, 0, 0))
        screen.blit(agent_id_text, (self.x - 25, self.y - 40))
        vil_image = pygame.image.load(f'images/{self.agent_id.lower()}.png')
        vil_image = pygame.transform.scale(vil_image, (60, 60))
        if not self.alive:
            vil_image = pygame.transform.rotate(vil_image, 90)
        screen.blit(vil_image, (self.x - 25, self.y - 25))

    def get_eliminated(self):
        """
        Eliminate the villager.
        """
        logger.info(f"{self.agent_id} has been eliminated!")
        self.add_killed_villagers(self)
        self.alive = False

    @staticmethod
    def add_killed_villagers(villager):
        """
        Add a villager to the list of killed villagers.

        Parameters:
            villager (Villager): The villager to add.
        """
        Villager.killed_villagers.append(villager)

class Werewolf(Villager):
    """
    Represents a werewolf in the game, inheriting from Villager.

    Attributes:
        is_werewolf (bool): Indicates if the villager is a werewolf.
        kill_cooldown (float): Cooldown timer for the werewolf's kill ability.
    """

    def __init__(self, agent_id, x, y, background_texts, llm: BaseLanguageModel, memory: AgentMemory, occupation="", meeting_location=(0, 0)):
        super().__init__(agent_id, x, y, background_texts, llm, memory, occupation, meeting_location)
        self.is_werewolf = True
        self.kill_cooldown = time.time()

    def update(self):
        """
        Update the werewolf's state.
        """
        if self.talking:
            return

        if self.task_doing:
            if self.task_complete():
                logger.info(f"{self.agent_id} (Werewolf) sabotaged the task '{self.current_task}'!")
                self.task_complete_function()
                self.current_task = None
                self.time_to_complete_task = None
                self.task_doing = False
        else:
            if self.current_task is not None:
                directions = [
                    (0, -1), (0, 1), (-1, 0), (1, 0),
                    (-1, -1), (-1, 1), (1, -1), (1, 1)
                ]
                current_distance = self.distance_to_target(self.x, self.y)
                moved = False

                for direction in directions:
                    next_x = self.x + SPEED * direction[0]
                    next_y = self.y + SPEED * direction[1]

                    if self.distance_to_target(next_x, next_y) < current_distance:
                        self.x = next_x
                        self.y = next_y
                        moved = True
                        break

                if not moved:
                    next_x = self.x + SPEED
                    next_y = self.y
                    if self.is_on_path(next_x, next_y, self.paths):
                        self.x = next_x
                        self.y = next_y

                if current_distance <= 2:
                    self.start_task()

class Player(Villager):
    """
    Represents a player in the game, inheriting from Villager.

    Attributes:
        speed (int): The speed at which the player moves.
    """

    def __init__(self, name, x, y, background_texts, llm: BaseLanguageModel, memory: AgentMemory, occupation="", meeting_location=(0, 0), paths=[]):
        super().__init__(name, x, y, background_texts, llm, memory, occupation, meeting_location, paths=paths)
        self.speed = 1

    def handle_input(self):
        """
        Handle player input for movement.
        """
        if not self.alive:
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
        """
        Update the player's state.
        """
        self.handle_input()
        super().update()

    def draw(self, screen):
        """
        Draw the player on the screen.

        Parameters:
            screen (pygame.Surface): The screen to draw on.
        """
        color = (0, 255, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)
        agent_id_text = self.font.render(self.agent_id, True, (0, 0, 0))
        screen.blit(agent_id_text, (self.x - 25, self.y - 40))

        vil_image = pygame.image.load('images/vil.png')
        vil_image = pygame.transform.scale(vil_image, (60, 60))
        screen.blit(vil_image, (self.x - 25, self.y - 25))
