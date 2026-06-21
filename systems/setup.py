from config import (
    WIDTH,
    HEIGHT,
    BLUE,
    RED,
    GOAL_WIDTH,
    GOAL_HEIGHT
)

from models.ball import Ball
from models.goal import Goal
from models.player import AIPlayer


def create_ball():
    """Создаёт мяч в центре поля"""

    return Ball(WIDTH // 2, HEIGHT // 2)


def create_goals():
    """Создаёт левые и правые ворота"""

    left_goal = Goal(
        0,
        HEIGHT // 2 - GOAL_HEIGHT // 2,
        GOAL_WIDTH,
        GOAL_HEIGHT,
        "LEFT"
    )

    right_goal = Goal(
        WIDTH - GOAL_WIDTH,
        HEIGHT // 2 - GOAL_HEIGHT // 2,
        GOAL_WIDTH,
        GOAL_HEIGHT,
        "RIGHT"
    )

    return left_goal, right_goal


def create_user_team():
    """Создаёт команду пользователя"""

    player1 = AIPlayer(WIDTH // 2 - 120, HEIGHT // 2, BLUE, "MIDFIELDER")
    player2 = AIPlayer(WIDTH // 2 - 80, HEIGHT // 2 - 150, BLUE, "ATTACKER")
    player3 = AIPlayer(WIDTH // 2 - 260, HEIGHT // 2 - 90, BLUE, "DEFENDER")
    player4 = AIPlayer(WIDTH // 2 - 80, HEIGHT // 2 + 150, BLUE, "ATTACKER")
    player5 = AIPlayer(WIDTH // 2 - 260, HEIGHT // 2 + 90, BLUE, "DEFENDER")

    return [player1, player2, player3, player4, player5]


def create_enemy_team():
    """Создаёт команду противника"""

    enemy1 = AIPlayer(WIDTH // 2 + 80, HEIGHT // 2 - 150, RED, "ATTACKER")
    enemy2 = AIPlayer(WIDTH // 2 + 120, HEIGHT // 2, RED, "MIDFIELDER")
    enemy3 = AIPlayer(WIDTH // 2 + 260, HEIGHT // 2 - 90, RED, "DEFENDER")
    enemy4 = AIPlayer(WIDTH // 2 + 80, HEIGHT // 2 + 150, RED, "ATTACKER")
    enemy5 = AIPlayer(WIDTH // 2 + 260, HEIGHT // 2 + 90, RED, "DEFENDER")

    return [enemy1, enemy2, enemy3, enemy4, enemy5]


def setup_team_zones(user_team, enemy_team):
    """Настраивает зоны движения для обеих команд"""

    for player in user_team:
        player.zone_x_min = 0
        player.zone_x_max = WIDTH * 0.6
        player.zone_y_min = 0
        player.zone_y_max = HEIGHT

    for player in enemy_team:
        player.zone_x_min = WIDTH * 0.4
        player.zone_x_max = WIDTH
        player.zone_y_min = 0
        player.zone_y_max = HEIGHT


def create_teams():
    """Создаёт обе команды и настраивает их зоны"""

    user_team = create_user_team()
    enemy_team = create_enemy_team()

    setup_team_zones(user_team, enemy_team)

    return user_team, enemy_team


def create_match_objects():
    """Создаёт основные объекты матча"""

    user_team, enemy_team = create_teams()
    ball = create_ball()
    left_goal, right_goal = create_goals()

    active_player = user_team[0]

    return user_team, enemy_team, ball, left_goal, right_goal, active_player