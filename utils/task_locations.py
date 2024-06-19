import pygame

class TaskLocation:
    def __init__(self, x, y, task, task_period):
        self.x = x
        self.y = y
        self.task = task
        self.task_period = task_period  # Time required to complete the task
        self.font = pygame.font.SysFont(None, 24)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), (self.x - 5, self.y - 5, 10, 10))
        task_text = self.font.render(self.task, True, (0, 0, 0), (255, 255, 255))  # Set white background color
        screen.blit(task_text, (self.x + 10, self.y - 10))

class Path:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (100, 100, 100)  # Gray color for the obstacle
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)