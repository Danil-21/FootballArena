import math

from config import (
    WIDTH,
    HEIGHT,
    GAME_TIME,
    PASS_FORCE,
    MANUAL_CONTROL_DISTANCE_OFFSET
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


def get_remaining_seconds(start_ticks, total_paused_time, pause_started, current_time):
    """Возвращает оставшееся время матча в секундах"""

    if start_ticks == 0:
        return GAME_TIME

    # Если сейчас игра стоит на паузе или после гола,
    # то текущая пауза тоже не должна входить в игровое время.
    current_pause_time = 0

    if pause_started != 0:
        current_pause_time = current_time - pause_started

    elapsed_ms = current_time - start_ticks - total_paused_time - current_pause_time
    remaining_seconds = GAME_TIME - elapsed_ms // 1000

    return max(0, remaining_seconds)