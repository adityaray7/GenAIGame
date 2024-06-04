import pygame
import time
from utils.gpt_query import get_query
class Villager:
    def __init__(self, agent_id, x, y, background_texts):
        self.agent_id = agent_id
        self.x = x
        self.y = y
        self.background_texts = background_texts
        self.current_task = None
        self.task_location = None
        self.task_start_time = None
        self.task_end_time = 111717403133    # random big number
        self.task_doing = False
        self.time_to_complete_task = None
        self.last_talk_attempt_time = 0
        self.talking = False
        self.font = pygame.font.SysFont(None, 24)

    def assign_task(self, task, location, time_to_complete_task):
        self.current_task = task
        self.task_location = (location.x, location.y)
        self.time_to_complete_task = time_to_complete_task
        self.task_doing = False
        self.task_start_time = None
        self.task_end_time = 111717403133

    # Returns True if the current time exceeds the end time of the task and False otherwise
    def task_complete(self):
        if self.current_task is None:
            return False  # No task assigned
        else:
            # Check if the current time exceeds the end time of the task
            return time.time() >= self.task_end_time

    # Records the start and end time of the task and sets the task_doing flag to True
    def start_task(self):
        # Record the start and end time of the task
        if not self.task_doing:
            print(f"{self.agent_id} has started to do the task '{self.current_task}'!")
            self.task_doing = True
            self.task_start_time = time.time()
            self.task_end_time = self.task_start_time + self.time_to_complete_task

    def update(self):
        if self.talking:
            return

        if self.task_doing:
            # Check if the task is complete
            if self.task_complete():
                print(f"\n{self.agent_id} has completed the task '{self.current_task}'!")
                self.current_task = None
                self.time_to_complete_task = None
                self.task_doing = False
        else:
            if self.current_task is not None:
                dx, dy = self.task_location[0] - self.x, self.task_location[1] - self.y
                dist = (dx**2 + dy**2)**0.5
                if dist > 1:
                    self.x += dx / dist
                    self.y += dy / dist
                else:
                    self.start_task()


    def draw(self, screen):
        color = (0, 0, 0) if self.task_doing else (255, 0, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 5)
        agent_id_text = self.font.render(self.agent_id, True, (0, 0, 0))
        screen.blit(agent_id_text, (self.x + 10, self.y))
        if self.current_task:
            task_text = self.font.render(self.current_task, True, (0, 0, 0))
            screen.blit(task_text, (self.x + 10, self.y - 20))  # Display the task text above the villager
        vil_image = pygame.image.load('images/vil.png')
        vil_image = pygame.transform.scale(vil_image, (75, 75))
        screen.blit(vil_image, (self.x, self.y))
            