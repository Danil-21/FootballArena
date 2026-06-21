import pygame

from config import (
    WIDTH,
    HEIGHT,
    WHITE,
    BLUE,
    RED,
    YELLOW,
    BUTTON_WIDTH,
    BUTTON_HEIGHT,
    MENU_START_BUTTON_Y,
    MENU_QUIT_BUTTON_Y,
    GAME_OVER_RESTART_BUTTON_Y,
    GAME_OVER_QUIT_BUTTON_Y
)


def draw_button(screen, font, rect, text):
    """Отрисовывает кнопку с рамкой и текстом"""

    pygame.draw.rect(screen, WHITE, rect, 2)

    button_text = font.render(text, True, WHITE)
    button_rect = button_text.get_rect(center=rect.center)

    screen.blit(button_text, button_rect)


def draw_small_text(screen, text, x, y):
    """Отрисовывает небольшой информационный текст"""

    small_font = pygame.font.SysFont("Arial", 24)
    rendered_text = small_font.render(text, True, WHITE)
    text_rect = rendered_text.get_rect(center=(x, y))

    screen.blit(rendered_text, text_rect)


def draw_menu_screen(screen, font, menu_image, start_button, quit_button):
    """Отрисовывает главное меню игры"""

    screen.blit(menu_image, (0, 0))

    title = font.render("FOOTBALL ARENA", True, WHITE)
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 170))
    screen.blit(title, title_rect)

    draw_button(screen, font, start_button, "Старт")
    draw_button(screen, font, quit_button, "Выход")

    draw_small_text(
        screen,
        "WASD — движение | SPACE — удар | TAB — смена игрока | P — пауза",
        WIDTH // 2,
        HEIGHT // 2 + 150
    )


def get_result_text(left_score, right_score):
    """Возвращает текст результата матча"""

    if left_score > right_score:
        return "Победа Синих"

    if right_score > left_score:
        return "Победа Красных"

    return "Ничья"


def get_result_color(left_score, right_score):
    """Возвращает цвет текста результата"""

    if left_score > right_score:
        return BLUE

    if right_score > left_score:
        return RED

    return YELLOW


def draw_game_over_screen(
    screen,
    font,
    menu_image,
    left_score,
    right_score,
    restart_button,
    quit_gameover_button
):
    """Отрисовывает экран окончания игры"""

    screen.blit(menu_image, (0, 0))

    result_text = font.render("Игра окончена", True, WHITE)
    result_rect = result_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180))
    screen.blit(result_text, result_rect)

    score_text = font.render(f"{left_score} : {right_score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120))
    screen.blit(score_text, score_rect)

    winner_text = get_result_text(left_score, right_score)
    winner_color = get_result_color(left_score, right_score)

    winner_rendered = font.render(winner_text, True, winner_color)
    winner_rect = winner_rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(winner_rendered, winner_rect)

    draw_button(screen, font, restart_button, "Заново")
    draw_button(screen, font, quit_gameover_button, "Выход")


def create_button(center_y):
    """Создаёт прямоугольник кнопки по вертикальной позиции центра"""

    return pygame.Rect(
        WIDTH // 2 - BUTTON_WIDTH // 2,
        center_y,
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )


def create_menu_buttons():
    """Создаёт кнопки главного меню"""

    start_button = create_button(MENU_START_BUTTON_Y)
    quit_button = create_button(MENU_QUIT_BUTTON_Y)

    return start_button, quit_button


def create_game_over_buttons():
    """Создаёт кнопки экрана окончания игры"""

    restart_button = create_button(GAME_OVER_RESTART_BUTTON_Y)
    quit_gameover_button = create_button(GAME_OVER_QUIT_BUTTON_Y)

    return restart_button, quit_gameover_button