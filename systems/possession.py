import math

from config import (
    CONTROL_DISTANCE_OFFSET,
    LOSE_CONTROL_MULTIPLIER,
    STEAL_DISTANCE,
    STEAL_THRESHOLD
)


def handle_ball_possession(player, ball, current_time):
    """
    Обрабатывает захват мяча, дриблинг, потерю контроля и отбор
    
    Args:
        player (Player): Игрок
        ball (Ball): Объект мяча
        current_time (int): Текущее игровое время
    """

    dx = ball.x - player.x
    dy = ball.y - player.y

    distance = math.hypot(dx, dy)

    control_distance = player.radius + ball.radius + CONTROL_DISTANCE_OFFSET

    if ball.owner == player and distance > control_distance * LOSE_CONTROL_MULTIPLIER:
        ball.owner = None
        player.has_ball = False
        ball.last_owner = player
        ball.release_time = current_time
        
        return

    if distance >= control_distance:
        return
    
    # Небольшая защита от мгновенного возврата мяча после паса или удара.
    if (
        ball.owner is None
        and ball.last_owner == player
        and current_time - ball.release_time < ball.release_cooldown
    ):
        return

    # Если мяч свободен - игрок подбирает его.
    if ball.owner is None:
        ball.owner = player
        player.has_ball = True
    # Если мячом владеет другой игрок - пробуем отобрать.
    elif ball.owner != player:
        old_owner = ball.owner

        steal_chance = max(0, 1 - distance / STEAL_DISTANCE)

        if steal_chance > STEAL_THRESHOLD:
            old_owner.has_ball = False
            ball.owner = player
            player.has_ball = True
    
    # Если после всех проверок этот игрок владеет мячом - выполняем дриблинг.
    if ball.owner == player:
        player.has_ball = True

        if distance != 0:
            dx /= distance
            dy /= distance

        # Мяч держится немного впереди игрока.
        target_x = player.x + dx * (player.radius + 18)
        target_y = player.y + dy * (player.radius + 18)

        # Плавное следование мяча за игроком.
        ball.vx += (target_x - ball.x) * 0.25
        ball.vy += (target_y - ball.y) * 0.25