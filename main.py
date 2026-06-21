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

TEAM_ATTACK = 'TEAM_ATTACK'
TEAM_DEFEND = 'TEAM_DEFEND'

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
        
        control_distance = self.radius + ball.radius + 15

        # Удар разрешён только если игрок рядом с мячом или владеет им
        if distance > control_distance and ball.owner != self:
            return

        # Нормализуем вектор удара
        dx /= distance
        dy /= distance

        kick_force = KICK_FORCE

        ball.vx = dx * kick_force
        ball.vy = dy * kick_force

        # После удара мяч больше не находится под контролем игрока
        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = pygame.time.get_ticks()


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


    def update(self, keys=None, ball=None, target_goal=None, teammates=None, enemies=None):
        """
        Обновление логики игрока AI
        """
        if self.task is None:
            return
        
        # task = getattr(self, 'task', 'SUPPORT')  # Получаем задачу, по умолчанию SUPPORT
        
        if self.task == 'PRESS':
            self.chase_ball(ball)
        elif self.task == 'ATTACK':
            self.attack(ball, target_goal, teammates, enemies)
        elif self.task == 'DEFEND':
            self.patrol_zone(ball)
        elif self.task == 'SUPPORT':
            self.move_to_support_position(ball)
        elif self.task == 'OPEN_FOR_PASS':
            self.open_for_pass(ball, target_goal, enemies)
        elif self.task == 'COVER':
            self.cover(ball)

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


    def attack(self, ball, target_goal, teammates, enemies):

        if ball is None or target_goal is None:
            return

        # Если игрок ещё не владеет мячом - сначала добежать до мяча
        if ball.owner != self:
            self.chase_ball(ball)
            return
        
        goal_x = target_goal.rect.centerx
        goal_y = target_goal.rect.centery

        distance_to_goal = math.hypot(self.x - goal_x, self.y - goal_y)

        teammate = self.find_best_teammate(teammates, ball, enemies, target_goal)

        # Если близко к воротам - бить
        if distance_to_goal < 320:
            self.kick_towards_goal(ball, target_goal)
            return
        
        # Если есть хороший пас - пасовать
        if teammate is not None and self.is_closer_to_goal(teammate, target_goal):
            self.pass_ball(ball, teammate)
            return
        
        # Иначе - двигаться к воротам
        self.move_towards(goal_x, goal_y, 0.8)

    
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
        """AI бьёт мяч в сторону ворот"""
        
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

        # После удара AI отпускает мяч
        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = pygame.time.get_ticks()

        
    def find_best_teammate(self, teammates, ball, enemies, target_goal):
        """Находит лучшего союзника для паса"""
        best_teammate = None
        best_score = -999999

        for teammate in teammates:
            
            if teammate == self:
                continue
            
            if not self.is_pass_safe(teammate, enemies):
                continue

            score = self.evaluate_pass(teammate, ball, enemies, target_goal)

            if score > best_score:
                best_score = score
                best_teammate = teammate

        return best_teammate
    

    def pass_ball(self, ball, teammate):
        """AI отдаёт пас партнёру"""

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

        # После паса мяч становится свободным
        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = pygame.time.get_ticks()


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


    def evaluate_pass(self, teammate, ball, enemies, target_goal):
        """Оценивает безопасность паса"""

        score = 0

        # Чем ближе партнёр к воротам соперника, тем лучше
        distance_to_goal = math.hypot(
            target_goal.rect.centerx - teammate.x,
            target_goal.rect.centery - teammate.y
        )
        score -= distance_to_goal * 1.5

        # Слишком дальний пас хуже
        pass_distance = math.hypot(teammate.x - ball.x, teammate.y - ball.y)
        score -= pass_distance * 0.4

        # Чем дальше ближайший соперник от партнёра, тем пас безопаснее
        if enemies:
            nearest_enemy = min(
                enemies,
                key=lambda e: math.hypot(e.x - teammate.x, e.y - teammate.y)
            )

            enemy_distance = math.hypot(
                nearest_enemy.x - teammate.x,
                nearest_enemy.y - teammate.y
            )

            score += enemy_distance * 3

        return score


    def is_pass_safe(self, teammate, enemies):

        ax = self.x
        ay = self.y

        bx = teammate.x
        by = teammate.y

        for enemy in enemies:

            ex = enemy.x
            ey = enemy.y

            abx = bx - ax
            aby = by - ay

            aex = ex - ax
            aey = ey - ay

            ab_len_sq = abx * abx + aby * aby

            if ab_len_sq == 0:
                continue

            t = (aex * abx + aey * aby) / ab_len_sq

            t = max(0, min(1, t))

            closest_x = ax + abx * t
            closest_y = ay + aby * t

            dx = ex - closest_x
            dy = ey - closest_y

            distance = math.sqrt(dx * dx + dy * dy)

            if distance < 50:
                return False

        return True


    def open_for_pass(self, ball, attack_goal, enemies):
        """Игрок открывается под пас в сторону ворот соперника"""
        if ball is None or attack_goal is None:
            return
        
        direction = 1 if attack_goal.rect.centerx > ball.x else -1

        target_x = ball.x + 160 * direction

        if self.home_y < HEIGHT // 2:
            target_y = ball.y - 90
        else:
            target_y = ball.y + 90

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.9)

    
    def cover(self, ball):
        """Защитник страхует команду во время атаки"""

        if ball is None:
            return

        # Защитник не летит к мячу, а держит позицию между своей зоной и мячом
        target_x = self.home_x * 0.7 + ball.x * 0.3
        target_y = self.home_y * 0.7 + ball.y * 0.3

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.6)


    def move_to_support_position(self, ball):
        """Игрок занимает позицию поддержки рядом с атакой"""

        if ball is None:
            return

        # Если домашняя позиция слева, команда чаще атакует вправо.
        # Если домашняя позиция справа, команда чаще атакует влево.
        attack_direction = 1 if self.home_x < WIDTH // 2 else -1

        # Поддержка располагается немного позади мяча
        target_x = ball.x - 120 * attack_direction
        target_y = self.home_y

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.7)


    def move_towards(self, target_x, target_y, speed_multiplier=1.0):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        dx /= dist
        dy /= dist

        self.x += dx * self.speed * speed_multiplier
        self.y += dy * self.speed * speed_multiplier


    def is_closer_to_goal(self, teammate, goal):
        my_dist = math.hypot(goal.rect.centerx - self.x, goal.rect.centery - self.y)
        teammate_dist = math.hypot(goal.rect.centerx - teammate.x, goal.rect.centery - teammate.y)
        
        return teammate_dist < my_dist


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.owner = None
        self.last_owner = None
        self.release_time = 0
        self.release_cooldown = 250 # Небольшая задержка, чтобы игрок не забрал мяч обратно мгновенно


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
    """Обрабатывает захват мяча, дриблинг, потерю контроля и отбор"""

    dx = ball.x - player.x
    dy = ball.y - player.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    control_distance = player.radius + ball.radius + 15

    # Если этот игрок не является владельцем, сбрасываем его флаг владения.
    # Это защищает от ситуации, когда has_ball остался True после отбора.
    if ball.owner != player:
        player.has_ball = False

    # Если владелец ушёл слишком далеко от мяча — он теряет контроль.
    # Это должно проверяться ДО условия distance < control_distance.
    if ball.owner == player and distance > control_distance * 1.5:
        ball.owner = None
        player.has_ball = False
        ball.last_owner = player
        ball.release_time = pygame.time.get_ticks()
        return

    # Если игрок далеко от мяча, он ничего не делает.
    if distance >= control_distance:
        return
    
    # Небольшая защита от мгновенного возврата мяча после паса или удара.
    if (
        ball.owner is None
        and ball.last_owner == player
        and pygame.time.get_ticks() - ball.release_time < ball.release_cooldown
    ):
        return

    # Если мяч свободен — игрок подбирает его.
    if ball.owner is None:
        ball.owner = player
        player.has_ball = True
    # Если мячом владеет другой игрок — пробуем отобрать.
    elif ball.owner != player:
        old_owner = ball.owner

        steal_chance = max(0, 1 - distance / 80)

        if steal_chance > 0.6:
            old_owner.has_ball = False
            ball.owner = player
            player.has_ball = True
    
    # Если после всех проверок этот игрок владеет мячом — выполняем дриблинг.
    if ball.owner == player:
        player.has_ball = True

        if distance != 0:
            dx /= distance
            dy /= distance

        # Мяч держится немного впереди игрока.
        target_x = player.x + dx * (player.radius + 18)
        target_y = player.y + dy * (player.radius + 18)

        # Плавное следование мяча за игроком.
        ball.vx += (target_x - ball.x) * 0.25
        ball.vy += (target_y - ball.y) * 0.25


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


def reset_positions(user_team, enemy_team, ball):
    """Сбрасывает позиции всех игроков и мяча после гола или рестарта"""
    user_positions = [
        (WIDTH // 2 - 120, HEIGHT // 2),
        (WIDTH // 2 - 80, HEIGHT // 2 - 150),
        (WIDTH // 2 - 260, HEIGHT // 2 - 90),
        (WIDTH // 2 - 80, HEIGHT // 2 + 150),
        (WIDTH // 2 - 260, HEIGHT // 2 + 90),
    ]

    enemy_positions = [
        (WIDTH // 2 + 80, HEIGHT // 2 - 150),
        (WIDTH // 2 + 120, HEIGHT // 2),
        (WIDTH // 2 + 260, HEIGHT // 2 - 90),
        (WIDTH // 2 + 80, HEIGHT // 2 + 150),
        (WIDTH // 2 + 260, HEIGHT // 2 + 90),
    ]

    # Сброс игроков команды пользователя
    for player, pos in zip(user_team, user_positions):
        player.x, player.y = pos
        player.home_x, player.home_y = pos
        player.has_ball = False
        player.task = 'SUPPORT'

    # Сброс игроков команды противника
    for player, pos in zip(enemy_team, enemy_positions):
        player.x, player.y = pos
        player.home_x, player.home_y = pos
        player.has_ball = False
        player.task = 'SUPPORT'

    # Сброс позиции мяча
    ball.x, ball.y = WIDTH // 2, HEIGHT // 2
    ball.vx = 0
    ball.vy = 0
    ball.owner = None
    ball.last_owner = None
    ball.release_time = 0


def assign_team_tasks(full_team, ball, own_goal, enemy_goal, controlled_players=None):
    """Назначает задачи игрокам команды в зависимости от ситуации на поле"""
    
    if controlled_players is None:
        controlled_players = full_team

    if not controlled_players:
        return
    
    # state = get_team_state(team, ball)

    team_has_ball = ball.owner in full_team
    enemy_has_ball = ball.owner is not None and ball.owner not in full_team

    closest_player = min(controlled_players,
                         key=lambda p: math.sqrt((p.x - ball.x) ** 2 + (p.y - ball.y) ** 2)
                         )

    for player in controlled_players:

        # Если этот AI владеет мячом
        if ball.owner == player:
            player.task = 'ATTACK'
        
        elif team_has_ball:
            if player.role in ('ATTACKER', 'MIDFIELDER'):
                player.task = 'OPEN_FOR_PASS'
            elif player.role == 'DEFENDER':
                player.task = 'COVER'
            else:
                player.task = 'SUPPORT'
        # Если мяч свободный
        elif ball.owner is None:
            if player == closest_player:
                player.task = 'PRESS'
            elif player.role == 'DEFENDER':
                player.task = 'DEFEND'
            else:
                player.task = 'SUPPORT'
        # Если противник владеет мячом
        elif enemy_has_ball:
            if player == closest_player:
                player.task = 'PRESS'
            elif player.role == 'DEFENDER':
                player.task = 'DEFEND'
            else:
                player.task = 'SUPPORT'


def get_team_state(team, ball):
    """Определяет, находится ли команда в атаке или защите"""
    if ball.owner in team:
        return TEAM_ATTACK
    
    return TEAM_DEFEND


def get_remaining_seconds(start_ticks, total_paused_time, pause_started):
    """Возвращает оставшееся время матча в секундах"""

    if start_ticks == 0:
        return GAME_TIME

    now = pygame.time.get_ticks()

    # Если сейчас игра стоит на паузе или после гола,
    # то текущая пауза тоже не должна входить в игровое время.
    current_pause_time = 0

    if pause_started != 0:
        current_pause_time = now - pause_started

    elapsed_ms = now - start_ticks - total_paused_time - current_pause_time
    remaining_seconds = GAME_TIME - elapsed_ms // 1000

    return max(0, remaining_seconds)


def draw_timer(seconds):
    """Отрисовывает таймер матча"""

    seconds = max(0, seconds)

    minutes = seconds // 60
    secs = seconds % 60

    timer_string = f"{minutes:02}:{secs:02}"

    time_text = font.render(timer_string, True, WHITE)
    time_rect = time_text.get_rect(center=(WIDTH // 2, 90))

    screen.blit(time_text, time_rect)


def main():
    running = True

    start_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 40, 240, 60)
    quit_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 40, 240, 60)
    restart_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2, 240, 60)
    quit_gameover_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 60)

    game_state = MENU
    reset_timer = 0

    # Время старта матча. Пока игра в меню, матч ещё не начался.
    start_ticks = 0

    # Общее время, которое матч провёл на паузе
    total_paused_time = 0

    # Время начала текущей паузы
    pause_started = 0

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
    player = AIPlayer(WIDTH // 2 - 120, HEIGHT // 2, BLUE, 'MIDFIELDER')
    player2 = AIPlayer(WIDTH // 2 - 80, HEIGHT // 2 - 150, BLUE, 'ATTACKER')
    player3 = AIPlayer(WIDTH // 2 - 260, HEIGHT // 2 - 90, BLUE, 'DEFENDER')
    player4 = AIPlayer(WIDTH // 2 - 80, HEIGHT // 2 + 150, BLUE, 'ATTACKER')
    player5 = AIPlayer(WIDTH // 2 - 260, HEIGHT // 2 + 90, BLUE, 'DEFENDER')

    # зоны USER TEAM
    # player2.zone_x_min = 0
    # player2.zone_x_max = WIDTH * 0.6
    # player2.zone_y_min = 0
    # player2.zone_y_max = HEIGHT

    # player3.zone_x_min = 0
    # player3.zone_x_max = WIDTH * 0.6
    # player3.zone_y_min = 0
    # player3.zone_y_max = HEIGHT
    
    # Команда противника
    enemy = AIPlayer(WIDTH // 2 + 80, HEIGHT // 2 - 150, RED, 'ATTACKER')
    enemy2 = AIPlayer(WIDTH // 2 + 120, HEIGHT // 2, RED, 'MIDFIELDER')
    enemy3 = AIPlayer(WIDTH // 2 + 260, HEIGHT // 2 - 90, RED, 'DEFENDER')
    enemy4 = AIPlayer(WIDTH // 2 + 80, HEIGHT // 2 + 150, RED, 'ATTACKER')
    enemy5 = AIPlayer(WIDTH // 2 + 260, HEIGHT // 2 + 90, RED, 'DEFENDER')

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

    user_team = [player, player2, player3, player4, player5]
    enemy_team = [enemy, enemy2, enemy3, enemy4, enemy5]

    # Зоны команды пользователя
    for p in user_team:
        p.zone_x_min = 0
        p.zone_x_max = WIDTH * 0.6
        p.zone_y_min = 0
        p.zone_y_max = HEIGHT

    # Зоны команды противника
    for p in enemy_team:
        p.zone_x_min = WIDTH * 0.4
        p.zone_x_max = WIDTH
        p.zone_y_min = 0
        p.zone_y_max = HEIGHT

    # Домашние позиции для игроков
    for p in user_team:
        p.home_x, p.home_y = p.x, p.y
    for p in enemy_team:
        p.home_x, p.home_y = p.x, p.y

    active_player = player

    while running:
        clock.tick(FPS)
        
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
        if not running:
            break

        if game_state == MENU:
            screen.blit(menu_image, (0, 0))

            title = font.render("FOOTBALL ARENA", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
            screen.blit(title, title_rect)

            # mouse = pygame.mouse.get_pos()

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

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game_state = PLAYING
                    start_ticks = pygame.time.get_ticks()
                    total_paused_time = 0
                    pause_started = 0

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.collidepoint(event.pos):
                        game_state = PLAYING
                        start_ticks = pygame.time.get_ticks()
                        total_paused_time = 0
                        pause_started = 0

                    if quit_button.collidepoint(event.pos):
                        running = False

            continue

        # События во время игры и паузы
        for event in events:
            
            # if event.type == pygame.QUIT:
            #     running = False

            # Удар по space
            if event.type == pygame.KEYDOWN:

                # Пауза работает и во время игры, и во время паузы
                if event.key == pygame.K_p:
                    if game_state == PLAYING:
                        game_state = PAUSED
                        pause_started = pygame.time.get_ticks()
                    elif game_state == PAUSED:
                        total_paused_time += pygame.time.get_ticks() - pause_started
                        pause_started = 0
                        game_state = PLAYING

                # Остальные игровые действия разрешены только во время PLAYING
                if game_state == PLAYING:
                    
                    # Удар по мячу активным игроком
                    if event.key == pygame.K_SPACE:
                        active_player.kick_ball(ball)

                    # Переключение активного игрока по TAB
                    if event.key == pygame.K_TAB:
                        index = user_team.index(active_player)
                        index = (index + 1) % len(user_team)
                        active_player = user_team[index]
                        for p in user_team:
                            p.task = None
        
        if game_state == PAUSED:
            # screen.blit(font.render("PAUSED", True, WHITE), (WIDTH//2 - 80, HEIGHT//2))
            # pygame.display.flip()

            draw_field()

            left_goal.draw(screen)
            right_goal.draw(screen)

            ball.draw(screen)

            for p in user_team + enemy_team:
                p.draw(screen)

            pygame.draw.circle(
                screen,
                (255, 255, 0),
                (int(active_player.x), int(active_player.y)),
                active_player.radius + 3,
                2
            )

            score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, 40))
            screen.blit(score_text, score_rect)

            pause_text = font.render("PAUSED", True, WHITE)
            pause_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(pause_text, pause_rect)

            remaining_seconds = get_remaining_seconds(
                start_ticks,
                total_paused_time,
                pause_started
            )

            draw_timer(remaining_seconds)

            pygame.display.flip()
            continue
        
        if game_state == GOAL_RESET:
            draw_field()

            left_goal.draw(screen)
            right_goal.draw(screen)
            ball.draw(screen)

            for p in user_team:
                p.draw(screen)
            for p in enemy_team:
                p.draw(screen)

             # Выделение активного игрока
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                (int(active_player.x), int(active_player.y)),
                active_player.radius + 3,
                2
            )

            # Счёт
            score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, 40))
            screen.blit(score_text, score_rect)

            # Надпись после гола
            goal_text = font.render("Гол!", True, WHITE)
            goal_rect = goal_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(goal_text, goal_rect)

            pygame.display.flip()

            # Через 1.5 секунды игра продолжается
            if pygame.time.get_ticks() - reset_timer > 1500:
                total_paused_time += pygame.time.get_ticks() - pause_started
                pause_started = 0
                game_state = PLAYING

            continue

        if game_state == GAME_OVER:
            screen.blit(menu_image, (0, 0))

            result_text = font.render("GAME OVER", True, WHITE)
            result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

            screen.blit(result_text, result_rect)
            screen.blit(score_text, score_rect)

            # mouse = pygame.mouse.get_pos()

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

            for event in events:
                # if event.type == pygame.QUIT:
                #     running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button.collidepoint(event.pos):
                        # сброс игры
                        left_score = 0
                        right_score = 0
                        reset_positions(user_team, enemy_team, ball)
                        active_player = player
                        start_ticks = pygame.time.get_ticks()
                        total_paused_time = 0
                        pause_started = 0
                        game_state = PLAYING

                    if quit_gameover_button.collidepoint(event.pos):
                        running = False

            continue
        
        remaining_seconds = get_remaining_seconds(
            start_ticks,
            total_paused_time,
            pause_started
        )

        if remaining_seconds <= 0:
            game_state = GAME_OVER
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
        assign_team_tasks(
                user_team,
                ball,
                left_goal,
                right_goal,
                controlled_players=ai_user_team
        )

        # Противники всегда под управлением AI, поэтому назначаем задачи всем
        assign_team_tasks(
            enemy_team,
            ball,
            right_goal,
            left_goal)

        ball.update()

        # Обновление только игроков, которыми управляет AI
        for p in user_team:
            if p == active_player:
                p.move(keys)
            else:
                p.update(ball=ball, target_goal=right_goal, teammates=user_team, enemies=enemy_team)
        # Противники всегда под управлением AI, поэтому обновляем всех
        for e in enemy_team:
            e.update(ball=ball, target_goal=left_goal, teammates=enemy_team, enemies=user_team)

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
            reset_positions(user_team, enemy_team, ball)
            game_state = GOAL_RESET
            reset_timer = pygame.time.get_ticks()
            pause_started = reset_timer
        if goal == 'RIGHT':
            right_score += 1
            reset_positions(user_team, enemy_team, ball)
            game_state = GOAL_RESET
            reset_timer = pygame.time.get_ticks()
            pause_started = reset_timer

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
        remaining_seconds = get_remaining_seconds(
            start_ticks,
            total_paused_time,
            pause_started
        )

        draw_timer(remaining_seconds)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
