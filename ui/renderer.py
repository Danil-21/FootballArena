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
    """

    screen.blit(field_image, (0, 0))


def draw_grid(screen):
    """Отрисовывает сетку для визуализации поля поиска пути"""

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
    """Отрисовывает мяч"""

    pygame.draw.circle(
        screen,
        WHITE,
        (int(ball.x), int(ball.y)),
        ball.radius
    )


def draw_goal(screen, goal):
    """Отрисовывает ворота"""

    pygame.draw.rect(screen, WHITE, goal.rect, 3)


def draw_player(screen, player):
    """Отрисовывает игрока"""

    pygame.draw.circle(
        screen,
        player.color,
        (int(player.x), int(player.y)),
        player.radius
    )


def draw_players(screen, user_team, enemy_team):
    """Отрисовывает всех игроков обеих команд"""

    for player in user_team + enemy_team:
        draw_player(screen, player)


def draw_active_player_marker(screen, active_player):
    """Отрисовывает обводку вокруг активного игрока"""

    pygame.draw.circle(
        screen,
        YELLOW,
        (int(active_player.x), int(active_player.y)),
        active_player.radius + 3,
        2
    )


def draw_score(screen, font, left_score, right_score):
    """Отрисовывает счёт матча"""

    score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, 40))

    screen.blit(score_text, score_rect)


def draw_timer(screen, font, seconds):
    """Отрисовывает таймер матча"""

    seconds = max(0, seconds)

    minutes = seconds // 60
    secs = seconds % 60

    timer_string = f"{minutes:02}:{secs:02}"

    time_text = font.render(timer_string, True, WHITE)
    time_rect = time_text.get_rect(center=(WIDTH // 2, 90))

    screen.blit(time_text, time_rect)


def draw_center_text(screen, font, text):
    """Отрисовывает текст по центру экрана"""

    rendered_text = font.render(text, True, WHITE)
    text_rect = rendered_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    screen.blit(rendered_text, text_rect)


def draw_game_scene(screen, field_image, user_team, enemy_team,
                    ball, left_goal, right_goal, active_player):
    """Отрисовывает основную игровую сцену"""

    draw_field(screen, field_image)
    draw_grid(screen)

    draw_goal(screen, left_goal)
    draw_goal(screen, right_goal)

    draw_ball(screen, ball)

    draw_players(screen, user_team, enemy_team)

    draw_active_player_marker(screen, active_player)
