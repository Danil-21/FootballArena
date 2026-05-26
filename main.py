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

GRID_SIZE = 40

CHASE_BALL = 'CHASE_BALL'
ATTACK = 'ATTACK'
RETURN_HOME = 'RETURN_HOME'

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
        self.has_ball = False


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


class AIPlayer(Player):
    
    def __init__(self, x, y, color):
        super().__init__(x, y, color)

        self.state = CHASE_BALL

        # домашняя позиция для возврата
        self.home_x = x
        self.home_y = y


    def update(self, ball, target_goal):

        # Расстояние до мяча
        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Выбор состояния

        # Если мяч рядом - атака
        if distance < 80:
            self.state = ATTACK

        # Если мяч очень далеко - домой
        elif distance > 400:
            self.state = RETURN_HOME

        # Иначе - догнать мяч
        else:
            self.state = CHASE_BALL

        # Поведение состояний
        if self.state == CHASE_BALL:
            self.chase_ball(ball)
        elif self.state == ATTACK:
            self.attack(ball, target_goal)
        elif self.state == RETURN_HOME:
            self.return_home()

        # Ограничение выхода за границы поля
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))


    def chase_ball(self, ball):
        
        next_cell = get_next_step(
            (self.x, self.y),
            (ball.x, ball.y)
        )

        target_x = next_cell[0] * GRID_SIZE + GRID_SIZE // 2
        target_y = next_cell[1] * GRID_SIZE + GRID_SIZE // 2

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return

        dx /= distance
        dy /= distance

        self.x += dx * self.speed
        self.y += dy * self.speed


    def attack(self, ball, target_goal):

        self.chase_ball(ball)

        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < self.radius + ball.radius + 5:
            self.kick_towards_goal(ball, target_goal)

    
    def return_home(self):

        dx = self.home_x - self.x
        dy = self.home_y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return
        
        dx /= distance
        dy /= distance

        self.x += dx * self.speed
        self.y += dy * self.speed
        

    def kick_towards_goal(self, ball, goal):

        # центр ворот
        target_x = goal.rect.centerx
        target_y = goal.rect.centery

        dx = target_x - ball.x
        dy = target_y - ball.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return

        # нормализация
        dx /= distance
        dy /= distance

        kick_force = 8

        ball.vx = dx * kick_force
        ball.vy = dy * kick_force


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
    

def resolve_collision(player1, player2):
    """Разрешает столкновение между двумя игроками"""

    dx = player2.x - player1.x
    dy = player2.y - player1.y

    distance = math.sqrt(dx ** 2 + dy ** 2)

    min_distance = player1.radius + player2.radius

    # Если нет столкновения
    if distance >= min_distance:
        return
    if distance == 0:
        return
    
    # Насколько объекты пересекаются
    overlap = min_distance - distance

    dx /= distance
    dy /= distance

    # Раздвигаем объекты
    player1.x -= dx * (overlap / 2)
    player1.y -= dy * (overlap / 2)

    player2.x += dx * (overlap / 2)
    player2.y += dy * (overlap / 2)


def handle_ball_possesion(player, ball):
    """Обрабатывает владение мячом"""

    dx = ball.x - player.x
    dy = ball.y - player.y

    distance = math.sqrt(dx ** 2 + dy ** 2)

    # Мяч рядом - игрок может владеть мячом
    if distance < player.radius + ball.radius + 8:
        player.has_ball = True

        # Позиция мяча перед игроком
        if distance != 0:
            dx /= distance
            dy /= distance

            offset = player.radius + ball.radius + 2

            ball.x = player.x + dx * offset
            ball.y = player.y + dy * offset


def to_grid(x, y):
    """"Преобразует пиксели в координаты сетки grid"""

    grid_x = int(x // GRID_SIZE)
    grid_y = int(y // GRID_SIZE)

    return (grid_x, grid_y)


def get_next_step(start, target):
    """Поиск следующего шага для пути"""

    start_grid = to_grid(start[0], start[1])
    target_grid = to_grid(target[0], target[1])

    current_x, current_y = start_grid
    target_x, target_y = target_grid

    # Движение по x
    if current_x < target_x:
        current_x += 1
    elif current_x > target_x:
        current_x -= 1

    # Движение по y
    if current_y < target_y:
        current_y += 1
    elif current_y > target_y:
        current_y -= 1

    return (current_x, current_y)


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

    # AI игрок
    enemy = AIPlayer(WIDTH // 2 + 150, HEIGHT // 2, RED)

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
        enemy.update(ball, left_goal)
        resolve_collision(player, enemy)
        handle_ball_possesion(player, ball)
        handle_ball_possesion(enemy, ball)

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
        
        # сетка
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(
                screen,
                (50, 180, 80),
                (x, 0),
                (x, HEIGHT)
            )

        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(
                screen,
                (50, 180, 80),
                (0, y),
                (WIDTH, y)
            )

        # Ворота
        left_goal.draw(screen)
        right_goal.draw(screen)
        
        # Объекты
        ball.draw(screen)
        player.draw(screen)
        enemy.draw(screen)
        
        # Счет
        score_text = font.render(f"{left_score} : {right_score}", True, WHITE)

        screen.blit(score_text, (WIDTH // 2 - 40, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
