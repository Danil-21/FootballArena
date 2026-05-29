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

if DIFFICULTY == "EASY":
    PLAYER_SPEED = 6
    kick_force = 10
elif DIFFICULTY == "HARD":
    PLAYER_SPEED = 5
    kick_force = 12
else:
    PLAYER_SPEED = 5
    kick_force = 10

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

DIFFICULTY = "NORMAL"

pygame.init()

field_image = pygame.image.load("FootballArena/assets/footballField.png")
field_image = pygame.transform.scale(field_image, (WIDTH, HEIGHT))
menu_image = pygame.image.load("FootballArena/assets/menuBack.jpg")
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
    
    def __init__(self, x, y, color, role):
        super().__init__(x, y, color)

        self.speed = PLAYER_SPEED - 2
        self.state = CHASE_BALL
        self.role = role
        self.defend_goal = None
        self.attack_goal = None

        # домашняя позиция для возврата
        self.home_x = WIDTH - 300
        self.home_y = HEIGHT // 2


    def update(self, ball, target_goal, teammates):

        # Расстояние до мяча
        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Выбор состояния
        if self.role == "ATTACKER":

            if not self.is_closest_to_ball(teammates, ball):
                self.state = RETURN_HOME

            if distance < 80:
                self.state = ATTACK
            elif distance > 400:
                self.state = RETURN_HOME
            else:
                self.state = CHASE_BALL
        elif self.role == "DEFENDER":
            # зона защиты (между мячом и воротами)
            goal_x = self.defend_goal.rect.centerx
            goal_y = self.defend_goal.rect.centery

            # расстояние до ворот (ВАЖНО!)
            ball_to_goal = math.sqrt(
                (ball.x - goal_x)**2 + (ball.y - goal_y)**2
            )

            # если мяч ближе к нашим воротам — защищаем
            if ball_to_goal < 350:
                self.state = CHASE_BALL
            else:
                self.state = RETURN_HOME

        # Поведение состояний
        if self.state == CHASE_BALL:
            self.chase_ball(ball)
        elif self.state == ATTACK:
            self.attack(ball, target_goal, teammates)
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
                self.kick_towards_goal(ball, self.attack_goal)

    
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

    control_distance = player.radius + ball.radius + 12

    # игрок контролирует мяч
    if distance < control_distance:

        player.has_ball = True

        # защита от деления на ноль
        if distance == 0:
            return

        # направление
        dx /= distance
        dy /= distance

        # точка контроля перед игроком
        target_x = player.x + dx * control_distance
        target_y = player.y + dy * control_distance

        # мягкое притягивание мяча
        follow_strength = 0.25

        ball.vx += (target_x - ball.x) * follow_strength * 0.1
        ball.vy += (target_y - ball.y) * follow_strength * 0.1

        # ВАЖНО: ограничиваем скорость
        max_speed = 6
        speed = math.sqrt(ball.vx**2 + ball.vy**2)

        if speed > max_speed:
            scale = max_speed / speed
            ball.vx *= scale
            ball.vy *= scale
    else:
        player.has_ball = False


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


def reset_positions(player, player2, enemy, enemy2, ball):
    player.x, player.y = WIDTH // 2 - 100, HEIGHT // 2 + 80
    player2.x, player2.y = WIDTH // 2 - 100, HEIGHT // 2 - 80

    enemy.x, enemy.y = WIDTH - 250, HEIGHT // 2 - 120
    enemy2.x, enemy2.y = WIDTH - 350, HEIGHT // 2 + 120

    ball.x, ball.y = WIDTH//2, HEIGHT//2
    ball.vx = 0
    ball.vy = 0


def main():
    running = True

    start_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 - 40, 240, 60)
    quit_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 40, 240, 60)
    restart_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2, 240, 60)
    quit_gameover_button = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 80, 240, 60)

    game_state = MENU
    reset_timer = 0

    start_ticks = pygame.time.get_ticks()

    player = Player(WIDTH // 2 - 100, HEIGHT // 2 + 80, BLUE)
    player2 = AIPlayer(WIDTH // 2 - 100, HEIGHT // 2 - 80, BLUE, 'ATTACKER')
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
    enemy = AIPlayer(WIDTH - 250, HEIGHT // 2 - 120, RED, 'ATTACKER')
    enemy2 = AIPlayer(WIDTH - 350, HEIGHT // 2 + 120, RED, 'DEFENDER')

    enemy.defend_goal = right_goal
    enemy.attack_goal = left_goal

    enemy2.defend_goal = right_goal
    enemy2.attack_goal = left_goal

    player2.defend_goal = left_goal
    player2.attack_goal = right_goal

    while running:
        clock.tick(FPS)

        if game_state == MENU:
            # screen.fill(GREEN)
            screen.blit(menu_image, (0, 0))

            title = font.render("FOOTBALL ARENA", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
            screen.blit(title, title_rect)

            mouse = pygame.mouse.get_pos()

            # START button
            pygame.draw.rect(screen, WHITE, start_button, 2)
            start_text = font.render("Старт", True, WHITE)
            # screen.blit(start_text, (start_button.x + 70, start_button.y + 10))
            start_rect = start_text.get_rect(center=start_button.center)
            screen.blit(start_text, start_rect)

            # QUIT button
            pygame.draw.rect(screen, WHITE, quit_button, 2)
            quit_text = font.render("Выход", True, WHITE)
            # screen.blit(quit_text, (quit_button.x + 80, quit_button.y + 10))
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
                if event.key == pygame.K_SPACE:
                    player.kick_ball(ball)
                if event.key == pygame.K_p:
                    if game_state == PLAYING:
                        game_state = PAUSED
                    elif game_state == PAUSED:
                        game_state = PLAYING
        
        if game_state == PAUSED:
            screen.blit(font.render("PAUSED", True, WHITE), (WIDTH//2 - 80, HEIGHT//2))
            pygame.display.flip()
            continue
        
        if game_state == GAME_OVER:
            screen.fill(GREEN)

            result_text = font.render("GAME OVER", True, WHITE)
            score_text = font.render(f"{left_score} : {right_score}", True, WHITE)

            screen.blit(result_text, (WIDTH // 2 - 120, HEIGHT // 2 - 150))
            screen.blit(score_text, (WIDTH // 2 - 80, HEIGHT // 2 - 100))

            mouse = pygame.mouse.get_pos()

            # RESTART
            pygame.draw.rect(screen, WHITE, restart_button, 2)
            restart_text = font.render("RESTART", True, WHITE)
            screen.blit(restart_text, (restart_button.x + 40, restart_button.y + 10))

            # QUIT
            pygame.draw.rect(screen, WHITE, quit_gameover_button, 2)
            quit_text = font.render("QUIT", True, WHITE)
            screen.blit(quit_text, (quit_gameover_button.x + 80, quit_gameover_button.y + 10))

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


        # Управление
        keys = pygame.key.get_pressed()
        player.move(keys)
        # player2.move(keys)

        # Обновление
        ball.update()
        enemies = [enemy, enemy2]
        players = [player, player2]
        enemy.update(ball, left_goal, enemies)
        enemy2.update(ball, left_goal, enemies)
        player2.update(ball, right_goal, players)

        resolve_collision(player, enemy)
        resolve_collision(player, enemy2)
        resolve_collision(enemy, enemy2)
        resolve_collision(player, player2)
        resolve_collision(player2, enemy)
        resolve_collision(player2, enemy2)

        handle_ball_possession(player, ball)
        handle_ball_possession(player2, ball)
        handle_ball_possession(enemy, ball)
        handle_ball_possession(enemy2, ball)

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
        player.draw(screen)
        player2.draw(screen)
        enemy.draw(screen)
        enemy2.draw(screen)
        
        # Счет
        score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
        # screen.blit(score_text, (WIDTH // 2 - 40, 20))
        score_rect = score_text.get_rect(center=(WIDTH // 2, 40))
        screen.blit(score_text, score_rect)

         # Таймер
        seconds = GAME_TIME - (pygame.time.get_ticks() - start_ticks) // 1000
        # time_text = font.render(f"Time: {seconds}", True, WHITE)
        minutes = seconds // 60
        secs = seconds % 60

        timer_string = f"{minutes:02}:{secs:02}"

        time_text = font.render(timer_string, True, WHITE)
        time_rect = time_text.get_rect(center=(WIDTH // 2, 90))
        screen.blit(time_text, time_rect)
        # screen.blit(time_text, (20, 20))
        if seconds <= 0:
            game_state = GAME_OVER

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
