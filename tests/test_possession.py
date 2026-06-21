from systems.setup import create_match_objects
from systems.possession import handle_ball_possession


def test_player_takes_free_ball_when_close_enough():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    player = user_team[0]

    ball.owner = None
    ball.last_owner = None
    ball.x = player.x + 5
    ball.y = player.y

    handle_ball_possession(player, ball, current_time=1000)

    assert ball.owner == player
    assert player.has_ball is True


def test_last_owner_cannot_immediately_retake_ball():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    player = user_team[0]

    ball.owner = None
    ball.last_owner = player
    ball.release_time = 1000

    ball.x = player.x + 5
    ball.y = player.y

    handle_ball_possession(player, ball, current_time=1100)

    assert ball.owner is None
    assert player.has_ball is False


def test_player_loses_control_when_ball_is_too_far():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    player = user_team[0]

    ball.owner = player
    player.has_ball = True

    ball.x = player.x + 200
    ball.y = player.y

    handle_ball_possession(player, ball, current_time=2000)

    assert ball.owner is None
    assert player.has_ball is False
    assert ball.last_owner == player
    assert ball.release_time == 2000


def test_player_can_steal_ball_from_opponent_when_close():
    user_team, enemy_team, ball, left_goal, right_goal, active_player = create_match_objects()

    old_owner = user_team[0]
    new_owner = enemy_team[0]

    ball.owner = old_owner
    old_owner.has_ball = True

    ball.x = new_owner.x
    ball.y = new_owner.y

    handle_ball_possession(new_owner, ball, current_time=3000)

    assert ball.owner == new_owner
    assert new_owner.has_ball is True
    assert old_owner.has_ball is False