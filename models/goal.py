import pygame


class Goal:
    """Модель ворот: хранит прямоугольник ворот и принадлежность стороне поля"""

    def __init__(self, x, y, width, height, team):
        """
        Создаёт объект ворот с прямоугольной областью и принадлежностью к стороне поля.
        
        Args:
            x (int | float): Координата левого верхнего угла ворот по оси X
            y (int | float): Координата левого верхнего угла ворот по оси Y
            width (int | float): Ширина ворот
            height (int | float): Высота ворот
            team (str): Сторона поля, к которой относятся ворота
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.team = team