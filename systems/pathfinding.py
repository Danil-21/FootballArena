from config import GRID_SIZE


def to_grid(x, y):
    """Преобразует пиксельные координаты в координаты сетки"""

    grid_x = int(x // GRID_SIZE)
    grid_y = int(y // GRID_SIZE)

    return grid_x, grid_y


def get_next_step(start, target):
    """Возвращает следующую клетку пути от start к target"""

    start = to_grid(start[0], start[1])
    target = to_grid(target[0], target[1])

    def heuristic(cell):
        return abs(cell[0] - target[0]) + abs(cell[1] - target[1])

    open_set = [start]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        # выбираем узел с минимальной стоимостью
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