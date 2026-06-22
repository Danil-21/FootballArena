from config import GRID_SIZE


def to_grid(x, y):
    """
    Преобразует пиксельные координаты в координаты сетки
    
    Args:
        x (int | float): Координата объекта по оси X в пикселях
        y (int | float): Координата объекта по оси Y в пикселях
    
    Returns:
        tuple[int, int]: Координаты клетки сетки
    """

    grid_x = int(x // GRID_SIZE)
    grid_y = int(y // GRID_SIZE)

    return grid_x, grid_y


def get_next_step(start, target):
    """
    Находит следующую клетку пути от начальной позиции к целевой позиции

    Args:
        start (tuple[int, int]): Начальная позиция в пикселях
        target (tuple[int, int]): Целевая позиция в пикселях

    Returns:
        tuple[int, int]: Координаты следующей клетки пути в сетке
    """

    start = to_grid(start[0], start[1])
    target = to_grid(target[0], target[1])

    def heuristic(cell):
        """
        Оценивает примерное расстояние от клетки до цели по Манхэттенской метрике
        
        Args:
            cell (tuple[int, int]): Координаты клетки сетки
        
        Returns:
            int: Приблизительное расстояние от клетки до цели
        """
        return abs(cell[0] - target[0]) + abs(cell[1] - target[1])

    open_set = [start]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        # узел с минимальной стоимостью
        current = min(open_set, key=lambda cell: g_score[cell] + heuristic(cell))

        if current == target:
            break

        open_set.remove(current)

        x, y = current

        for nx, ny in [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]:
            neighbor = (nx, ny)
            new_cost = g_score[current] + 1

            if neighbor not in g_score or new_cost < g_score[neighbor]:
                g_score[neighbor] = new_cost
                came_from[neighbor] = current

                if neighbor not in open_set:
                    open_set.append(neighbor)
    
    # восстановление одного шага пути
    node = target
    path = []

    while node in came_from:
        path.append(node)
        node = came_from[node]

    path.reverse()

    return path[0] if path else start