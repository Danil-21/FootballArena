from config import GAME_TIME

from systems.setup import create_match_objects
from systems.game_logic import (
    goal_check,
    reset_positions,
    get_remaining_seconds,
    assign_team_tasks
)


def test_goal_check_left_to_right():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    ball.x = left_goal.rect.centerx
    ball.y = left_goal.rect.centery

    result = goal_check(ball, left_goal, right_goal)

    assert result == "RIGHT"


def test_goal_check_right_to_left():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    ball.x = right_goal.rect.centerx
    ball.y = right_goal.rect.centery

    result = goal_check(ball, left_goal, right_goal)

    assert result == "LEFT"


def test_goal_check_when_ball_is_not_in_goal():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    ball.x = 600
    ball.y = 350

    result = goal_check(ball, left_goal, right_goal)

    assert result is None


def test_reset_positions():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    ball.owner = user_team[0]
    ball.last_owner = user_team[0]
    ball.release_time = 1000
    ball.vx = 5
    ball.vy = -3

    reset_positions(user_team, enemy_team, ball)

    assert ball.owner is None
    assert ball.last_owner is None
    assert ball.release_time == 0
    assert ball.vx == 0
    assert ball.vy == 0

    for player in user_team + enemy_team:
        assert player.has_ball is False
        assert player.task == "SUPPORT"


def test_timer_counts_down_without_pause():
    start_ticks = 1000
    total_paused_time = 0
    pause_started = 0
    current_time = 11000

    remaining = get_remaining_seconds(
        start_ticks,
        total_paused_time,
        pause_started,
        current_time
    )

    assert remaining == GAME_TIME - 10


def test_timer_does_not_count_current_pause_time():
    start_ticks = 1000
    total_paused_time = 0
    pause_started = 5000
    current_time = 9000

    remaining = get_remaining_seconds(
        start_ticks,
        total_paused_time,
        pause_started,
        current_time
    )

    # Прошло 8 секунд реального времени,
    # но 4 секунды из них игра стояла на паузе.
    assert remaining == GAME_TIME - 4


def test_assign_team_tasks_sets_only_one_press_when_ball_is_free():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    ball.owner = None
    ball.x = user_team[0].x
    ball.y = user_team[0].y

    assign_team_tasks(
        full_team=user_team,
        ball=ball,
        own_goal=left_goal,
        enemy_goal=right_goal,
        controlled_players=user_team
    )

    press_players = [
        player for player in user_team
        if player.task == "PRESS"
    ]

    assert len(press_players) == 1