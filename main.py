from turtle import title

import pygame
import sys
import math


WIDTH = 1200
HEIGHT = 700
FPS = 60

GAME_TIME = 120

MENU = "MENU"
PLAYING = "PLAYING"
PAUSED = "PAUSED"
GOAL_RESET = "GOAL_RESET"
GAME_OVER = "GAME_OVER"

DIFFICULTY = "NORMAL"

GAME_CONFIG = {
    "EASY": {
        "player_speed": 6,
        "kick_force": 9
    },
    "NORMAL": {
        "player_speed": 5,
        "kick_force": 10
    },
    "HARD": {
        "player_speed": 4,
        "kick_force": 12
    }
}

config = GAME_CONFIG[DIFFICULTY]

GREEN = (30, 160, 60)
WHITE = (255, 255, 255)
BLUE = (50, 80, 255)
RED = (255, 50, 50)

PLAYER_RADIUS = 20
PLAYER_SPEED = config["player_speed"]
KICK_FORCE = config["kick_force"]

BALL_RADIUS = 10
BALL_FRICTION = 0.98

GOAL_WIDTH = 20
GOAL_HEIGHT = 200

GRID_SIZE = 40

CHASE_BALL = 'CHASE_BALL'
ATTACK = 'ATTACK'
RETURN_HOME = 'RETURN_HOME'

DIFFICULTY = "NORMAL"

pygame.init()

field_image = pygame.image.load("assets/footballField.png")
field_image = pygame.transform.scale(field_image, (WIDTH, HEIGHT))
menu_image = pygame.image.load("assets/menuBack.jpg")
menu_image = pygame.transform.scale(menu_image, (WIDTH, HEIGHT))

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
        self.role = 'USER'


    def move(self, keys):
        if not keys:
            return
        
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

            kick_force = KICK_FORCE

            ball.vx = dx * kick_force
            ball.vy = dy * kick_force


    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            self.radius
        )


    def update(self, keys=None, ball=None, target_goal=None, teammates=None):
        if keys is not None:
            self.move(keys)


class AIPlayer(Player):
    
    def __init__(self, x, y, color, role):
        super().__init__(x, y, color)

        self.speed = PLAYER_SPEED - 2
        self.state = CHASE_BALL
        self.role = role
        self.task = 'SUPPORT'   # <-- ДОБАВИТЬ ЭТО (защита от ошибки)
        self.defend_goal = None
        self.attack_goal = None

        self.zone_x_min = 0
        self.zone_x_max = WIDTH
        self.zone_y_min = 0
        self.zone_y_max = HEIGHT

        # домашняя позиция для возврата
        self.home_x = WIDTH - 300
        self.home_y = HEIGHT // 2


    def update(self, keys=None, ball=None, target_goal=None, teammates=None):
        """
        Обновление логики игрока AI
        """
        if self.task is None:
            return
        
        task = getattr(self, 'task', 'SUPPORT')  # Получаем задачу, по умолчанию SUPPORT
        
        if task == 'PRESS':
            self.chase_ball(ball)
        elif task == 'ATTACK':
            self.attack(ball, target_goal, teammates)
        elif task == 'DEFEND':
            self.patrol_zone(ball)
        elif task == 'SUPPORT':
            # в позицию поддержки
            support_x = self.home_x + 50
            support_y = self.home_y
            dx = support_x - self.x
            dy = support_y - self.y
            dist = math.sqrt(dx ** 2 + dy ** 2)
            if dist != 0:
                dx /= dist
                dy /= dist
                self.x += dx * self.speed
                self.y += dy * self.speed

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


    def attack(self, ball, target_goal, teammates):

        self.chase_ball(ball)

        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Если мяч рядом
        if distance < self.radius + ball.radius + 5:
            
            teammate = self.find_best_teammate(teammates, ball)

            # Если союзник ближе к воротам
            if teammate is not None and teammate.x < self.x:
                self.pass_ball(ball, teammate)
            else:
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

        
    def find_best_teammate(self, teammates, ball):

        best_teammate = None
        best_score = -999999

        for teammate in teammates:
            if teammate == self:
                continue
            # Чем левее, тем ближе к воротам противника
            score = 0

            # ближе к воротам — лучше
            score += (WIDTH - teammate.x) * 2

            # ближе к мячу — лучше
            score -= abs(teammate.x - ball.x)
            score -= abs(teammate.y - ball.y)

            if score > best_score:
                best_score = score
                best_teammate = teammate

        return best_teammate
    

    def pass_ball(self, ball, teammate):

        dx = teammate.x - ball.x
        dy = teammate.y - ball.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return
        
        dx /= distance
        dy /= distance

        pass_force = 7

        ball.vx = dx * pass_force
        ball.vy = dy * pass_force


    def is_closest_to_ball(self, teammates, ball):

        my_dist = math.sqrt((self.x - ball.x)**2 + (self.y - ball.y)**2)

        for t in teammates:
            if t == self:
                continue
            if abs(t.x - ball.x) < my_dist:
                return False

        return True


    def patrol_zone(self, ball):
        """Движение внутри своей зоны даже без мяча"""
        # смещение относительно мяча (чтобы не стоял)
        target_x = self.x
        target_y = self.y

        # если мяч в зоне - смещаемся к нему сбоку
        if self.zone_x_min < ball.x < self.zone_x_max:

            offset_y = 60 if self.role == 'DEFENDER' else -60

            target_x = ball.x
            target_y = ball.y + offset_y

        else:
            # возвращение в центр зоны
            target_x = (self.zone_x_min + self.zone_x_max) / 2
            target_y = (self.zone_y_min + self.zone_y_max) / 2

        dx = target_x - self.x
        dy = target_y - self.y

        dist = math.sqrt(dx ** 2 + dy ** 2)
        if dist != 0:
            dx /= dist
            dy /= dist

            self.x += dx * self.speed * 0.7
            self.y += dy * self.speed * 0.7


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.owner = None


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
    # screen.fill(GREEN)
    screen.blit(field_image, (0, 0))

    # Центральная линия
    # pygame.draw.line(screen, WHITE,
    #                  ((WIDTH // 2), 0),
    #                  (WIDTH // 2, HEIGHT), 
    #                  3
    #                  )
    
    # # Центральный круг
    # pygame.draw.circle(screen, WHITE,
    #                    (WIDTH // 2, HEIGHT // 2),
    #                    80, 
    #                    3
    #                    )
    

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


def handle_ball_possession(player, ball):
    """Обрабатывает владение мячом"""

    dx = ball.x - player.x
    dy = ball.y - player.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    control_distance = player.radius + ball.radius + 15

    # игрок контролирует мяч
    if distance < control_distance:

        # если мяч никем не занят - захват
        if ball.owner is None:
            ball.owner = player

        # если уже владеет этот игрок - дриблинг
        if ball.owner == player:

            player.has_ball = True

            # направление движения игрока (упрощённо)
            if distance != 0:
                dx /= distance
                dy /= distance

            # мяч держится ПЕРЕД игроком (важно для футбольного ощущения)
            target_x = player.x + dx * (player.radius + 18)
            target_y = player.y + dy * (player.radius + 18)

            # плавное следование мяча за игроком
            ball.vx += (target_x - ball.x) * 0.25
            ball.vy += (target_y - ball.y) * 0.25
        
        # если мячом владеет другой игрок - отбор
        elif ball.owner != player:

            # шанс отбора зависит от дистанции
            steal_chance = max(0, 1 - (distance / 80))

            if steal_chance > 0.6:  # порог для успешного отбора
                ball.owner = player
        
        else:
            # если ушёл далеко — потерял контроль
            if ball.owner == player:
                ball.owner = None
                player.has_ball = False


def to_grid(x, y):
    """"Преобразует пиксели в координаты сетки grid"""

    grid_x = int(x // GRID_SIZE)
    grid_y = int(y // GRID_SIZE)

    return (grid_x, grid_y)


def get_next_step(start, target):
    start = to_grid(start[0], start[1])
    target = to_grid(target[0], target[1])

    def h(a):
        return abs(a[0] - target[0]) + abs(a[1] - target[1])

    open_set = [start]
    came_from = {}

    g = {start: 0}

    while open_set:
        # выбираем узел с минимальной стоимостью
        current = min(open_set, key=lambda n: g[n] + h(n))

        if current == target:
            break

        open_set.remove(current)

        x, y = current
        for nx, ny in [(x+1,y), (x-1,y), (x,y+1), (x,y-1)]:
            neighbor = (nx, ny)

            new_cost = g[current] + 1

            if neighbor not in g or new_cost < g[neighbor]:
                g[neighbor] = new_cost
                came_from[neighbor] = current
                if neighbor not in open_set:
                    open_set.append(neighbor)

    # восстановление одного шага пути
    node = target
    path = []

    while node in came_from:
        path.append(node)
        node = came_from[node]

    path.reverse()

    return path[0] if path else start


def goal_check(ball, left_goal, right_goal):
    """Проверяет, забит ли гол"""

    # Проверяем левые ворота
    if left_goal.rect.collidepoint(ball.x, ball.y):
        return 'RIGHT'
    
    # Проверяем правые ворота
    if right_goal.rect.collidepoint(ball.x, ball.y):
        return 'LEFT'
    
    return None


def reset_positions(player, player2, enemy, enemy2, ball):
    player.x, player.y = WIDTH // 2 - 100, HEIGHT // 2 + 80
    player2.x, player2.y = WIDTH // 2 - 100, HEIGHT // 2 - 80

    enemy.x, enemy.y = WIDTH - 250, HEIGHT // 2 - 120
    enemy2.x, enemy2.y = WIDTH - 350, HEIGHT // 2 + 120

    ball.x, ball.y = WIDTH//2, HEIGHT//2
    ball.vx = 0
    ball.vy = 0


def assign_team_tasks(team, ball, own_goal, enemy_goal):
    """Назначает задачи игрокам команды в зависимости от ситуации на поле"""
    closest_player = min(team, key=lambda p: math.sqrt((p.x - ball.x)**2 + (p.y - ball.y)**2))

    for player in team:
        if player == closest_player:
            player.task = 'PRESS'
        elif player.role == 'ATTACKER':
            player.task = 'ATTACK'
        elif player.role == 'DEFENDER':
            player.task = 'DEFEND'
        else:
            player.task = 'SUPPORT'


def main():
    running = True

    start_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 40, 240, 60)
    quit_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 40, 240, 60)
    restart_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2, 240, 60)
    quit_gameover_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 60)

    game_state = MENU
    reset_timer = 0

    start_ticks = pygame.time.get_ticks()

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

    # Команда пользователя
    player = AIPlayer(WIDTH // 2 - 100, HEIGHT // 2 + 80, BLUE, 'MIDFIELDER')
    player2 = AIPlayer(WIDTH // 2 - 100, HEIGHT // 2 - 80, BLUE, 'ATTACKER')
    player3 = AIPlayer(WIDTH // 2 - 200, HEIGHT // 2, BLUE, 'DEFENDER')

    # зоны USER TEAM
    player2.zone_x_min = 0
    player2.zone_x_max = WIDTH * 0.6
    player2.zone_y_min = 0
    player2.zone_y_max = HEIGHT

    player3.zone_x_min = 0
    player3.zone_x_max = WIDTH * 0.6
    player3.zone_y_min = 0
    player3.zone_y_max = HEIGHT
    
    # Команда противника
    enemy = AIPlayer(WIDTH - 250, HEIGHT // 2 - 120, RED, 'ATTACKER')
    enemy2 = AIPlayer(WIDTH - 350, HEIGHT // 2 + 120, RED, 'MIDFIELDER')
    enemy3 = AIPlayer(WIDTH - 250, HEIGHT // 2, RED, 'DEFENDER')

    enemy.zone_x_min = WIDTH * 0.4
    enemy.zone_x_max = WIDTH
    enemy.zone_y_min = 0
    enemy.zone_y_max = HEIGHT

    enemy2.zone_x_min = WIDTH * 0.4
    enemy2.zone_x_max = WIDTH
    enemy2.zone_y_min = 0
    enemy2.zone_y_max = HEIGHT

    enemy3.zone_x_min = WIDTH * 0.4
    enemy3.zone_x_max = WIDTH
    enemy3.zone_y_min = 0
    enemy3.zone_y_max = HEIGHT

    user_team = [player, player2, player3]
    enemy_team = [enemy, enemy2, enemy3]



    # Домашние позиции для AI
    for p in user_team[1:]:
        p.home_x, p.home_y = p.x, p.y
    for p in enemy_team:
        p.home_x, p.home_y = p.x, p.y

    active_player = player

    while running:
        clock.tick(FPS)

        if game_state == MENU:
            screen.blit(menu_image, (0, 0))

            title = font.render("FOOTBALL ARENA", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
            screen.blit(title, title_rect)

            mouse = pygame.mouse.get_pos()

            # START button
            pygame.draw.rect(screen, WHITE, start_button, 2)
            start_text = font.render("Старт", True, WHITE)
            start_rect = start_text.get_rect(center=start_button.center)
            screen.blit(start_text, start_rect)

            # QUIT button
            pygame.draw.rect(screen, WHITE, quit_button, 2)
            quit_text = font.render("Выход", True, WHITE)
            quit_rect = quit_text.get_rect(center=quit_button.center)
            screen.blit(quit_text, quit_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = PLAYING

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(event.pos):
                        game_state = PLAYING

                    if quit_button.collidepoint(event.pos):
                        running = False

            continue

        # Обработка событий
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False

            # Удар по space
            if event.type == pygame.KEYDOWN:

                # Удар по мячу активным игроком
                if event.key == pygame.K_SPACE:
                    active_player.kick_ball(ball)
                
                # Пауза по P
                if event.key == pygame.K_p:
                    if game_state == PLAYING:
                        game_state = PAUSED
                    elif game_state == PAUSED:
                        game_state = PLAYING
                
                # Переключение активного игрока по TAB
                if event.key == pygame.K_TAB:
                    index = user_team.index(active_player)
                    index = (index + 1) % len(user_team)
                    active_player = user_team[index]
                    for p in user_team:
                        p.task = None
        
        if game_state == PAUSED:
            screen.blit(font.render("PAUSED", True, WHITE), (WIDTH//2 - 80, HEIGHT//2))
            pygame.display.flip()
            continue
        
        if game_state == GAME_OVER:
            screen.blit(menu_image, (0, 0))

            result_text = font.render("GAME OVER", True, WHITE)
            result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

            screen.blit(result_text, result_rect)
            screen.blit(score_text, score_rect)

            mouse = pygame.mouse.get_pos()

            # RESTART
            pygame.draw.rect(screen, WHITE, restart_button, 2)
            restart_text = font.render("RESTART", True, WHITE)
            restart_rect = restart_text.get_rect(center=restart_button.center)
            screen.blit(restart_text, restart_rect)

            # QUIT
            pygame.draw.rect(screen, WHITE, quit_gameover_button, 2)
            quit_text = font.render("QUIT", True, WHITE)
            quit_rect = quit_text.get_rect(center=quit_gameover_button.center)
            screen.blit(quit_text, quit_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button.collidepoint(event.pos):
                        # сброс игры
                        left_score = 0
                        right_score = 0
                        reset_positions(player, player2, enemy, enemy2, ball)
                        start_ticks = pygame.time.get_ticks()
                        game_state = PLAYING

                    if quit_gameover_button.collidepoint(event.pos):
                        running = False

            continue


        # Управление активным игроком

        keys = pygame.key.get_pressed()
        # active_player.update(keys=keys)
        
        # Союзники, которыми сейчас управляет AI.
        # Активного игрока сюда не добавляем, потому что им управляет пользователь.
        for p in user_team:
            if p != active_player:
                p.task = None
        
        ai_user_team = [p for p in user_team if p != active_player]
        
        # Назначаем задачи только тем союзникам, которые сейчас под управлением AI
        assign_team_tasks(ai_user_team, ball, left_goal, right_goal)

        # Противники всегда под управлением AI, поэтому назначаем задачи всем
        assign_team_tasks(enemy_team, ball, right_goal, left_goal)

        ball.update()

        # Обновление только игроков, которыми управляет AI
        for p in user_team:
            if p == active_player:
                p.move(keys)
            else:
                p.update(ball=ball, target_goal=right_goal, teammates=user_team)
        # Противники всегда под управлением AI, поэтому обновляем всех
        for e in enemy_team:
            e.update(ball=ball, target_goal=left_goal, teammates=enemy_team)

        # Столкновения между игроками
        all_players = user_team + enemy_team
        for i, player_1 in enumerate(all_players):
            for player_2 in all_players[i+1:]:
                resolve_collision(player_1, player_2)
            handle_ball_possession(player_1, ball)

        # Проверка гола
        goal = goal_check(ball, left_goal, right_goal)

        if goal == 'LEFT':
            left_score += 1
            reset_positions(player, player2, enemy, enemy2, ball)
            game_state = GOAL_RESET
            reset_timer = pygame.time.get_ticks()
        if goal == 'RIGHT':
            right_score += 1
            reset_positions(player, player2, enemy, enemy2, ball)
            game_state = GOAL_RESET
            reset_timer = pygame.time.get_ticks()

        # Отрисовка
        draw_field()
        # сетка
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(
                screen,
                (40, 120, 60),
                (x, 0),
                (x, HEIGHT)
            )
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(
                screen,
                (40, 120, 60),
                (0, y),
                (WIDTH, y)
            )

        # Ворота
        left_goal.draw(screen)
        right_goal.draw(screen)
        
        # Объекты
        ball.draw(screen)
        for p in all_players:
            p.draw(screen)
        
        # Отрисовка выделения активного игрока
        pygame.draw.circle(screen, (255, 255, 0), (int(active_player.x), int(active_player.y)), active_player.radius+3, 2)

        # Счет
        score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 40))
        screen.blit(score_text, score_rect)

         # Таймер
        seconds = GAME_TIME - (pygame.time.get_ticks() - start_ticks) // 1000
        minutes = seconds // 60
        secs = seconds % 60
        timer_string = f"{minutes:02}:{secs:02}"
        time_text = font.render(timer_string, True, WHITE)
        time_rect = time_text.get_rect(center=(WIDTH // 2, 90))
        screen.blit(time_text, time_rect)
        if seconds <= 0:
            game_state = GAME_OVER

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
