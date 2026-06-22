import pygame
import sys

from config import *

from systems.setup import create_match_objects
from systems.physics import resolve_collision
from systems.possession import handle_ball_possession
from systems.game_logic import (
    goal_check,
    reset_positions,
    assign_team_tasks,
    get_remaining_seconds,
    find_closest_player_to_ball
)

from ui.renderer import (
    draw_game_scene,
    draw_score,
    draw_timer,
    draw_center_text
)

from ui.screens import (
    draw_menu_screen,
    draw_game_over_screen,
    draw_pause_screen,
    create_menu_buttons,
    create_game_over_buttons,
    create_pause_buttons
)


pygame.init()

field_image = pygame.image.load("assets/footballField.png")
field_image = pygame.transform.scale(field_image, (WIDTH, HEIGHT))
menu_image = pygame.image.load("assets/menuBack.jpg")
menu_image = pygame.transform.scale(menu_image, (WIDTH, HEIGHT))

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Arena")

clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 40)


def get_player_movement(keys):
    """
    Возвращает направление движения игрока по клавишам
    
    Args:
    keys (pygame.key): состояние клавиш клавиатуры

    Returns:
        tuple: направление движения (x, y)
    """

    move_x = 0
    move_y = 0

    if keys[pygame.K_a]:
        move_x -= 1

    if keys[pygame.K_d]:
        move_x += 1

    if keys[pygame.K_w]:
        move_y -= 1

    if keys[pygame.K_s]:
        move_y += 1

    return move_x, move_y


def main():
    """
    Основной игровой цикл.

    Управляет:
    - состояниями игры (MENU, PLAYING, PAUSED, GAME_OVER)
    - обработкой событий
    - обновлением AI и физики
    - проверкой голов и таймера
    - отрисовкой сцены
    """

    running = True

    start_button, quit_button = create_menu_buttons()
    restart_button, quit_gameover_button = create_game_over_buttons()
    pause_resume_button, pause_restart_button, pause_quit_button = create_pause_buttons()

    game_state = MENU
    reset_timer = 0
    start_ticks = 0
    total_paused_time = 0
    pause_started = 0

    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    left_score = 0
    right_score = 0

    for p in user_team:
        p.zone_x_min = 0
        p.zone_x_max = WIDTH * 0.6
        p.zone_y_min = 0
        p.zone_y_max = HEIGHT

    for p in enemy_team:
        p.zone_x_min = WIDTH * 0.4
        p.zone_x_max = WIDTH
        p.zone_y_min = 0
        p.zone_y_max = HEIGHT

    for p in user_team:
        p.home_x, p.home_y = p.x, p.y
    for p in enemy_team:
        p.home_x, p.home_y = p.x, p.y

    while running:
        clock.tick(FPS)
        
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
        if not running:
            break
        
        current_time = pygame.time.get_ticks()
        pause_started_this_frame = False

        if game_state == MENU:

            draw_menu_screen(
                screen,
                font,
                menu_image,
                start_button,
                quit_button
            )

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

        # События во время PLAYING
        for event in events:

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and game_state == PLAYING:
                    game_state = PAUSED
                    pause_started = current_time
                    pause_started_this_frame = True
                    continue

                if game_state == PLAYING:
                    if event.key == pygame.K_SPACE:
                        active_player.kick_ball(ball, pygame.time.get_ticks())

                    if event.key == pygame.K_TAB:
                        closest_player = find_closest_player_to_ball(user_team, ball)

                        if closest_player is not None:
                            active_player = closest_player
                            active_player.task = None
        
        if game_state == PAUSED:
            draw_game_scene(
                screen,
                field_image,
                user_team,
                enemy_team,
                ball,
                left_goal,
                right_goal,
                active_player
            )

            draw_score(screen, font, left_score, right_score)

            remaining_seconds = get_remaining_seconds(
                start_ticks,
                total_paused_time,
                pause_started,
                pygame.time.get_ticks()
            )

            draw_timer(screen, font, remaining_seconds)
            
            draw_pause_screen(
                screen,
                font,
                pause_resume_button,
                pause_restart_button,
                pause_quit_button
            )

            pygame.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p and not pause_started_this_frame:
                        total_paused_time += current_time - pause_started
                        pause_started = 0
                        game_state = PLAYING

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pause_resume_button.collidepoint(event.pos):
                        total_paused_time += current_time - pause_started
                        pause_started = 0
                        game_state = PLAYING

                    if pause_restart_button.collidepoint(event.pos):
                        left_score = 0
                        right_score = 0

                        reset_positions(user_team, enemy_team, ball)

                        active_player = user_team[0]

                        start_ticks = current_time
                        total_paused_time = 0
                        pause_started = 0

                        game_state = PLAYING

                    if pause_quit_button.collidepoint(event.pos):
                        running = False

            continue
        
        if game_state == GOAL_RESET:
            draw_game_scene(
                screen,
                field_image,
                user_team,
                enemy_team,
                ball,
                left_goal,
                right_goal,
                active_player
            )

            draw_score(screen, font, left_score, right_score)

            remaining_seconds = get_remaining_seconds(
                start_ticks,
                total_paused_time,
                pause_started,
                pygame.time.get_ticks()
            )

            draw_timer(screen, font, remaining_seconds)
            draw_center_text(screen, font, "Гол!")

            pygame.display.flip()

            # Через 1.5 секунды игра продолжается
            if pygame.time.get_ticks() - reset_timer > GOAL_RESET_COOLDOWN:
                total_paused_time += pygame.time.get_ticks() - pause_started
                pause_started = 0
                game_state = PLAYING

            continue

        if game_state == GAME_OVER:
            draw_game_over_screen(
                screen,
                font,
                menu_image,
                left_score,
                right_score,
                restart_button,
                quit_gameover_button
            )

            pygame.display.flip()

            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if restart_button.collidepoint(event.pos):
                        # сброс игры
                        left_score = 0
                        right_score = 0
                        reset_positions(user_team, enemy_team, ball)
                        active_player = user_team[0]
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
            pause_started,
            current_time
        )

        if remaining_seconds <= 0:
            game_state = GAME_OVER
            continue

        # Управление активным игроком
        keys = pygame.key.get_pressed()
        
        for p in user_team:
            if p != active_player:
                p.task = None
        
        ai_user_team = [p for p in user_team if p != active_player]
        
        # Задачи только AI
        assign_team_tasks(
                user_team,
                ball,
                left_goal,
                right_goal,
                controlled_players=ai_user_team
        )
        assign_team_tasks(
            enemy_team,
            ball,
            right_goal,
            left_goal
        )

        ball.update()

        # Обновление только игроков, которыми управляет AI
        move_x, move_y = get_player_movement(keys)
        for p in user_team:
            if p == active_player:
                p.move(move_x, move_y)
            else:
                p.update(
                    ball=ball,
                    target_goal=right_goal,
                    teammates=user_team,
                    enemies=enemy_team,
                    current_time=current_time
                )

        for e in enemy_team:
            e.update(
                ball=ball,
                target_goal=left_goal,
                teammates=enemy_team,
                enemies=user_team,
                current_time=current_time
            )

        # Столкновения
        all_players = user_team + enemy_team
        for i, player_1 in enumerate(all_players):
            for player_2 in all_players[i+1:]:
                resolve_collision(player_1, player_2)
            handle_ball_possession(player_1, ball, current_time)

        goal = goal_check(ball, left_goal, right_goal)

        if goal == 'LEFT':
            left_score += 1
            reset_positions(user_team, enemy_team, ball)
            game_state = GOAL_RESET
            reset_timer = current_time
            pause_started = current_time
        if goal == 'RIGHT':
            right_score += 1
            reset_positions(user_team, enemy_team, ball)
            game_state = GOAL_RESET
            reset_timer = current_time
            pause_started = current_time

        # Отрисовка
        draw_game_scene(
            screen,
            field_image,
            user_team,
            enemy_team,
            ball,
            left_goal,
            right_goal,
            active_player
        )

        draw_score(screen, font, left_score, right_score)

        remaining_seconds = get_remaining_seconds(
            start_ticks,
            total_paused_time,
            pause_started,
            pygame.time.get_ticks()
        )

        draw_timer(screen, font, remaining_seconds)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
