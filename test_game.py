import pygame
pygame.init()

from main import (
    BLUE,
    Player,
    Ball,
    Goal,
    get_next_step,
    resolve_collision,
    goal_check
)


def test_astar_returns_step():
    step = get_next_step((100, 100), (200, 100))
    assert isinstance(step, tuple)


def test_collision_separates_players():
    p1 = Player(100, 100, BLUE)
    p2 = Player(110, 100, BLUE)

    resolve_collision(p1, p2)

    assert p1.x != p2.x


def test_goal_detection():
    ball = Ball(10, 300)
    left_goal = Goal(0, 200, 20, 200, "LEFT")
    right_goal = Goal(1180, 200, 20, 200, "RIGHT")

    assert goal_check(ball, left_goal, right_goal) == "RIGHT"