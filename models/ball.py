from config import *


class Ball:
    """Модель мяча: хранит координаты, скорость, радиус и владельца"""

    def __init__(self, x, y):
        """
        Создаёт объект мяча с начальными координатами, скоростью и параметрами владения.
        
        Args:
            x (int | float): Начальная координата мяча по оси X
            y (int | float): Начальная координата мяча по оси Y
        """
        self.x = x
        self.y = y

        self.vx = 0
        self.vy = 0

        self.radius = BALL_RADIUS

        self.owner = None
        self.last_owner = None
        self.release_time = 0
        self.release_cooldown = RELEASE_COOLDOWN # Небольшая задержка, чтобы игрок не забрал мяч обратно мгновенно


    def update(self):
        """Обновляет положение мяча и обрабатывает отскок от границ поля"""
        # Движение мяча
        self.x += self.vx
        self.y += self.vy

        # Трение
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION

        # Отскок от стен
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx *= -1

        if self.x + self.radius >= WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1

        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy *= -1

        if self.y + self.radius >= HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy *= -1