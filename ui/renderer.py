import pygame

from config import (
    WIDTH,
    HEIGHT,
    WHITE,
    YELLOW,
    GRID_SIZE,
    SHOW_GRID,
    GRID_COLOR
)


def draw_field(screen, field_image):
    """
    Рисует футбольное поле

    Args:
        screen (pygame.Surface): Поверхность для отрисовки 
        field_image (pygame.Surface): Изображение поля
    """

    screen.blit(field_image, (0, 0))


def draw_grid(screen):
    """
    Отрисовывает сетку для визуализации поля поиска пути
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
    """

    if not SHOW_GRID:
        return

    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (x, 0),
            (x, HEIGHT)
        )

    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (0, y),
            (WIDTH, y)
        )


def draw_ball(screen, ball):
    """
    Отрисовывает мяч
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        ball (Ball): Объект мяча
    """

    pygame.draw.circle(
        screen,
        WHITE,
        (int(ball.x), int(ball.y)),
        ball.radius
    )


def draw_goal(screen, goal):
    """
    Отрисовывает ворота
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        goal (Goal): Объект ворот
    """

    pygame.draw.rect(screen, WHITE, goal.rect, 3)


def draw_player(screen, player):
    """
    Отрисовывает игрока
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        player (Player): Игрок
    """

    pygame.draw.circle(
        screen,
        player.color,
        (round(player.x), round(player.y)),
        player.radius
    )

    font = pygame.font.SysFont("Arial", 16, bold=True)
    text = font.render(str(player.number), True, (0, 0, 0))

    text_rect = text.get_rect(
        center=(
            round(player.x),
            round(player.y)
        )
    )

    screen.blit(text, text_rect)


def draw_players(screen, user_team, enemy_team):
    """
    Отрисовывает всех игроков обеих команд
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        user_team (list): Игроки команды пользователя
        enemy_team (list): Игроки команды противника
    """

    for player in user_team + enemy_team:
        draw_player(screen, player)


def draw_active_player_marker(screen, active_player):
    """
    Отрисовывает обводку вокруг активного игрока
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        active_player (Player): Текущий выбранный игрок
    """

    pygame.draw.circle(
        screen,
        YELLOW,
        (int(active_player.x), int(active_player.y)),
        active_player.radius + 3,
        2
    )


def draw_score(screen, font, left_score, right_score):
    """
    Отрисовывает счёт матча
    
    Args: 
        screen (pygame.Surface): Поверхность для отрисовки
        font (pygame.font.Font): Шрифт текста
        left_score (int): Голы левой команды
        right_score (int): Голы правой команды
    """

    score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 10, 50))

    screen.blit(score_text, score_rect)


def draw_timer(screen, font, seconds):
    """
    Отрисовывает таймер матча
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        font (pygame.font.Font): Шрифт текста
        seconds (int): Оставшееся время
    """

    seconds = max(0, seconds)

    minutes = seconds // 60
    secs = seconds % 60

    timer_string = f"{minutes:02}:{secs:02}"

    time_text = font.render(timer_string, True, WHITE)
    time_rect = time_text.get_rect(center=(WIDTH // 10, 90))

    screen.blit(time_text, time_rect)


def draw_center_text(screen, font, text):
    """
    Отрисовывает текст по центру экрана
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        font (pygame.font.Font): Шрифт текста
        text (str): Текст для отображения
    """

    rendered_text = font.render(text, True, WHITE)
    text_rect = rendered_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    screen.blit(rendered_text, text_rect)


def draw_game_scene(screen, field_image, user_team, enemy_team,
                    ball, left_goal, right_goal, active_player):
    """
    Отрисовывает основную игровую сцену
    
    Args:
        screen (pygame.Surface): Поверхность для отрисовки
        field_image (pygame.Surface): Изображение футбольного поля
        user_team (list): Игроки команды пользователя
        enemy_team (list): Игроки команды противника
        ball (Ball): Объект мяча
        left_goal (Goal): Левые ворота
        right_goal (Goal): Правые ворота
        active_player (Player): Активный игрок
    """

    draw_field(screen, field_image)
    draw_grid(screen)

    draw_goal(screen, left_goal)
    draw_goal(screen, right_goal)

    draw_ball(screen, ball)

    draw_players(screen, user_team, enemy_team)

    draw_active_player_marker(screen, active_player)
