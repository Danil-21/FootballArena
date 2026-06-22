import math


def resolve_collision(player1, player2):
    """
    Разрешает столкновение между двумя игроками, если их круги пересекаются

    Args:
        player1 (Player): Первый игрок
        player2 (Player): Второй игрок
    """

    dx = player2.x - player1.x
    dy = player2.y - player1.y

    distance = math.hypot(dx, dy)

    min_distance = player1.radius + player2.radius

    # Если нет столкновения
    if distance >= min_distance:
        return
    if distance == 0:
        return
    
    # Насколько объекты пересекаются
    overlap = min_distance - distance

    dx /= distance
    dy /= distance

    # Раздвигаем объекты
    player1.x -= dx * (overlap / 2)
    player1.y -= dy * (overlap / 2)

    player2.x += dx * (overlap / 2)
    player2.y += dy * (overlap / 2)