import pygame

class Task:
    def __init__(self, x, y, task, task_period):
        self.x = x
        self.y = y
        self.task = task
        self.task_period = task_period  # Time required to complete the task
        self.font = pygame.font.SysFont(None, 24)
        self.completed = False
        self.sabotaged = False

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x - 5, self.y - 5, 10, 10))
        if (self.sabotaged):
            task_text = self.font.render(self.task, True, (0, 0, 0), (255,20, 20))  # Set red background color
        elif (self.completed):
            task_text = self.font.render(self.task, True, (0, 0, 0), (20, 255, 20))  # Set green background color
        else:
            task_text = self.font.render(self.task, True, (0, 0, 0), (255, 255, 255))  # Set white background color
        screen.blit(task_text, (self.x + 10, self.y - 10))
    
    def complete(self):
        self.completed = True
        self.sabotaged = False
        print(f"{self.task} was completed through the transferred functions")

    def sabotage(self):
        self.completed = False
        self.sabotaged = True
        print(f"{self.task} was sabotaged through the transferred functions")
