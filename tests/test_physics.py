import math

from config import BLUE, RED, PLAYER_RADIUS
from models.player import AIPlayer
from systems.physics import resolve_collision


def test_resolve_collision_separates_overlapping_players():
    player1 = AIPlayer(100, 100, BLUE, "DEFENDER")
    player2 = AIPlayer(100 + PLAYER_RADIUS, 100, RED, "ATTACKER")

    resolve_collision(player1, player2)

    distance = math.hypot(
        player2.x - player1.x,
        player2.y - player1.y
    )

    min_distance = player1.radius + player2.radius

    assert distance >= min_distance - 0.001


def test_resolve_collision_does_not_move_distant_players():
    player1 = AIPlayer(100, 100, BLUE, "DEFENDER")
    player2 = AIPlayer(300, 100, RED, "ATTACKER")

    old_player1_position = (player1.x, player1.y)
    old_player2_position = (player2.x, player2.y)

    resolve_collision(player1, player2)

    assert (player1.x, player1.y) == old_player1_position
    assert (player2.x, player2.y) == old_player2_position