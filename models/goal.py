import pygame


class Goal:
    """Модель ворот: хранит прямоугольник ворот и принадлежность стороне поля"""

    def __init__(self, x, y, width, height, team):
        self.rect = pygame.Rect(x, y, width, height)
        self.team = team