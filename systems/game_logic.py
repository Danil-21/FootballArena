import math

from config import (
    WIDTH,
    HEIGHT,
    GAME_TIME
)


def goal_check(ball, left_goal, right_goal):
    """
    Проверяет, забит ли гол в одни из ворот

    Args:
        ball (Ball): Объект мяча
        left_goal (Goal): Левые ворота
        right_goal (Goal): Правые ворота
    
    Returns:
        str: 'LEFT' или 'RIGHT' в зависимости от забитого гола, либо None
    """

    if left_goal.rect.collidepoint(ball.x, ball.y):
        return 'RIGHT'

    if right_goal.rect.collidepoint(ball.x, ball.y):
        return 'LEFT'
    
    return None


def reset_positions(user_team, enemy_team, ball):
    """
    Сбрасывает позиции всех игроков и мяча после гола или рестарта
    
    Args:
        user_team (list): Команда пользователя
        enemy_team (list): Команда противника
        ball (Ball): Объект мяча
    """

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

    for player, pos in zip(user_team, user_positions):
        player.x, player.y = pos
        player.home_x, player.home_y = pos
        player.has_ball = False
        player.task = 'SUPPORT'

    for player, pos in zip(enemy_team, enemy_positions):
        player.x, player.y = pos
        player.home_x, player.home_y = pos
        player.has_ball = False
        player.task = 'SUPPORT'

    ball.x, ball.y = WIDTH // 2, HEIGHT // 2
    ball.vx = 0
    ball.vy = 0
    ball.owner = None
    ball.last_owner = None
    ball.release_time = 0


def assign_team_tasks(full_team, ball, own_goal, enemy_goal, controlled_players=None):
    """
    Назначает задачи игрокам команды в зависимости от ситуации на поле
    
    Args:
        full_team (list): Все игроки команды
        ball (Ball): Объект мяча
        own_goal (Goal): Свои ворота
        enemy_goal (Goal): Ворота соперника
        controlled_players (list): Игроки, которым назначаются задачи
    """
    
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
    """
    Возвращает оставшееся время матча в секундах
    
    Args:
        start_ticks (int): Время начала матча
        total_paused_time (int): Общее время всех пауз
        pause_started (int): Время начала текущей паузы
        current_time (int): Текущее время игры
    
    Returns:
        int: Оставшееся время в секундах
    """

    if start_ticks == 0:
        return GAME_TIME

    current_pause_time = 0

    if pause_started != 0:
        current_pause_time = current_time - pause_started

    elapsed_ms = current_time - start_ticks - total_paused_time - current_pause_time
    remaining_seconds = GAME_TIME - elapsed_ms // 1000

    return max(0, remaining_seconds)


def find_closest_player_to_ball(players, ball):
    """
    Находит игрока, который находится ближе всего к мячу
    
    Args:
        players (list): Список игроков
        ball (Ball): Объект мяча
    
    Returns:
        Player: Ближайший игрок или None, если список пуст
    """

    if not players:
        return None

    return min(
        players,
        key=lambda player: math.hypot(
            player.x - ball.x,
            player.y - ball.y
        )
    )