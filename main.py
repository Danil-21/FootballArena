import pygame
import sys
import math


WIDTH = 1200
HEIGHT = 700
FPS = 60

GREEN = (30, 160, 60)
WHITE = (255, 255, 255)
BLUE = (50, 80, 255)
RED = (255, 50, 50)

PLAYER_RADIUS = 20
PLAYER_SPEED = 5

BALL_RADIUS = 10
BALL_FRICTION = 0.98

GOAL_WIDTH = 20
GOAL_HEIGHT = 200

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Arena")

clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 40)


class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED


    def move(self, keys):
        # По x
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        # По y
        if keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_s]:
            self.y += self.speed

        # Ограничение выхода за границы поля
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    
    def kick_ball(self, ball):
        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return
        
        # Удар только если мяч рядом
        if distance < self.radius + ball.radius + 10:

            # Нормализуем вектор удара
            dx /= distance
            dy /= distance

            kick_force = 10

            ball.vx = dx * kick_force
            ball.vy = dy * kick_force


    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            self.radius
        )


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS


    def update(self):
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


    def draw(self, screen):
        pygame.draw.circle(
            screen,
            WHITE,
            (int(self.x), int(self.y)),
            self.radius
        )

class Goal:
    """Класс для ворот"""
    def __init__(self, x, y, width, height, team):
        self.rect = pygame.Rect(x, y, width, height)
        self.team = team


    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, 3)


def draw_field():
    """
    Рисует футбольное поле с разметкой
    """
    screen.fill(GREEN)

    # Центральная линия
    pygame.draw.line(screen, WHITE,
                     ((WIDTH // 2), 0),
                     (WIDTH // 2, HEIGHT), 
                     3
                     )
    
    # Центральный круг
    pygame.draw.circle(screen, WHITE,
                       (WIDTH // 2, HEIGHT // 2),
                       80, 
                       3
                       )
    

def goal_check(ball, left_goal, right_goal):
    """Проверяет, забит ли гол"""

    # Проверяем левые ворота
    if left_goal.rect.collidepoint(ball.x, ball.y):
        return 'RIGHT'
    
    # Проверяем правые ворота
    if right_goal.rect.collidepoint(ball.x, ball.y):
        return 'LEFT'
    
    return None


def main():
    running = True

    player = Player(WIDTH // 2, HEIGHT // 2, BLUE)
    ball = Ball(WIDTH // 2 + 150, HEIGHT // 2)

    # Ворота
    left_goal = Goal(
        0,
        HEIGHT // 2 - GOAL_HEIGHT // 2,
        GOAL_WIDTH,
        GOAL_HEIGHT,
        'LEFT'
    )

    right_goal = Goal(
        WIDTH - GOAL_WIDTH,
        HEIGHT // 2 - GOAL_HEIGHT // 2,
        GOAL_WIDTH,
        GOAL_HEIGHT,
        'RIGHT'
    )

    # Счет
    left_score = 0
    right_score = 0

    while running:
        clock.tick(FPS)

        # Обработка событий
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False

            # Удар по space
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.kick_ball(ball)
        
        # Управление
        keys = pygame.key.get_pressed()
        player.move(keys)

        # Обновление
        ball.update()

        # Проверка гола
        goal = goal_check(ball, left_goal, right_goal)

        if goal == 'LEFT':
            left_score += 1

            # Сброс мяча в центр
            ball.x = WIDTH // 2
            ball.y = HEIGHT // 2

            ball.vx = 0
            ball.vy = 0
        
        if goal == 'RIGHT':
            right_score += 1

            # Сброс мяча в центр
            ball.x = WIDTH // 2
            ball.y = HEIGHT // 2

            ball.vx = 0
            ball.vy = 0

        # Отрисовка
        draw_field()
        
        # Ворота
        left_goal.draw(screen)
        right_goal.draw(screen)
        
        # Объекты
        ball.draw(screen)
        player.draw(screen)
        
        # Счет
        score_text = font.render(f"{left_score} : {right_score}", True, WHITE)

        screen.blit(score_text, (WIDTH // 2 - 40, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
