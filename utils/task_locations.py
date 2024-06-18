import pygame

class Task:
    def __init__(self, x, y, task, task_period):
        self.x = x
        self.y = y
        self.task = task
        self.task_period = task_period  # Time required to complete the task
        self.font = pygame.font.SysFont(None, 24)
        self.completed = False

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x - 5, self.y - 5, 10, 10))
        task_text = self.font.render(self.task, True, (0, 0, 0), (255, 255, 255))  # Set white background color
        screen.blit(task_text, (self.x + 10, self.y - 10))
    
    def complete(self):
        self.completed = True
        print("task was completed through the transferred functions")
