import math

from config import *
from systems.pathfinding import get_next_step


class Player:
    """Базовая модель игрока"""

    def __init__(self, x, y, color):
        """
        Создаёт базового игрока с координатами, цветом, радиусом,
        скоростью и состоянием владения мячом
        
        Args: 
            x (int | float): Начальная координата игрока по оси X
            y (int | float): Начальная координата игрока по оси Y
            color (tuple): Цвет игрока
        """

        self.x = x
        self.y = y
        self.color = color
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED
        self.has_ball = False
        self.role = 'USER'


    def distance_to(self, obj):
        """
        Возвращает расстояние от игрока до другого объекта
        
        Args:
            obj (object): Объект, у которого есть координаты x и y
        
        Returns:
            float: Расстояние между игроком и переданным объектом
        """

        return math.hypot(self.x - obj.x, self.y - obj.y)


    def limit_to_field(self):
        """Ограничивает позицию игрока границами игрового поля"""

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))


    def move(self, move_x, move_y):
        """
        Двигает игрока по заданному направлению
        
        Args:
            move_x (int | float): Направление движения по оси X
            move_y (int | float): Направление движения по оси Y
        """
        
        self.x += move_x * self.speed
        self.y += move_y * self.speed

        self.limit_to_field()

    
    def kick_ball(self, ball, current_time):
        """
        Удар игрока по мячу
        
        Args:
            ball (Ball): Объект мяча
            current_time (int): Текущее игровое время
        """

        dx = ball.x - self.x
        dy = ball.y - self.y

        distance = self.distance_to(ball)

        if distance == 0:
            return
        
        control_distance = self.radius + ball.radius + CONTROL_DISTANCE_OFFSET

        # Удар разрешён только если игрок рядом с мячом или владеет им
        if distance > control_distance and ball.owner != self:
            return

        # Нормализуем вектор удара
        dx /= distance
        dy /= distance

        ball.vx = dx * KICK_FORCE
        ball.vy = dy * KICK_FORCE

        # После удара мяч больше не находится под контролем игрока
        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = current_time

    
class AIPlayer(Player):
    """Игрок с искусственным интеллектом"""

    def __init__(self, x, y, color, role, number):
        """
        Создаёт AI-игрока
        
        Args:
            x (int | float): Начальная координата игрока по оси X
            y (int | float): Начальная координата игрока по оси Y
            color (tuple[int, int, int]): Цвет игрока
            role (str): Роль игрока в команде
        """
        
        super().__init__(x, y, color)

        self.speed = PLAYER_SPEED - AI_SPEED_PENALTY
        self.role = role
        self.number = number
        self.task = 'SUPPORT'
        
        self.defend_goal = None
        self.attack_goal = None

        self.zone_x_min = 0
        self.zone_x_max = WIDTH
        self.zone_y_min = 0
        self.zone_y_max = HEIGHT

        self.home_x = x
        self.home_y = y


    def update(self, ball=None, target_goal=None, teammates=None, enemies=None, current_time=0):
        """
        Обновляет поведение AI-игрока в зависимости от текущей задачи
        
        Args:
            ball (Ball): Объект мяча
            target_goal (Goal): Ворота, которые атакует игрок
            teammates (list): Список партнёров по команде
            enemies (list): Список игроков соперника
            current_time (int): Текущее игровое
        """
        
        if self.task is None:
            return

        if self.task == 'PRESS':
            self.chase_ball(ball)
        elif self.task == 'ATTACK':
            self.attack(ball, target_goal, teammates, enemies, current_time)
        elif self.task == 'DEFEND':
            self.patrol_zone(ball)
        elif self.task == 'SUPPORT':
            self.move_to_support_position(ball)
        elif self.task == 'OPEN_FOR_PASS':
            self.open_for_pass(ball, target_goal, enemies)
        elif self.task == 'COVER':
            self.cover(ball)

        self.limit_to_field()


    def chase_ball(self, ball):
        """
        Двигает AI-игрока к мячу с использованием следующей клетки пути
        
        Args:
            ball (Ball): Объект мяча
        """

        if ball is None:
            return
        
        next_cell = get_next_step(
            (self.x, self.y),
            (ball.x, ball.y)
        )

        target_x = next_cell[0] * GRID_SIZE + GRID_SIZE // 2
        target_y = next_cell[1] * GRID_SIZE + GRID_SIZE // 2

        self.move_towards(target_x, target_y)


    def attack(self, ball, target_goal, teammates, enemies, current_time):
        """
        Управляет поведением AI-игрока в атаке: движение к мячу, удар,
        пас или продвижение к воротам.
        
        Args:
            ball (Ball): Объект мяча
            target_goal (Goal): Ворота соперника
            teammates (list): Список партнёров по команде
            enemies (list): Список игроков соперника
            current_time (int): Текущее игровое время
        """

        if ball is None or target_goal is None:
            return

        if ball.owner != self:
            self.chase_ball(ball)
            return
        
        goal_x = target_goal.rect.centerx
        goal_y = target_goal.rect.centery

        distance_to_goal = math.hypot(self.x - goal_x, self.y - goal_y)

        teammate = self.find_best_teammate(teammates, ball, enemies, target_goal)

        if distance_to_goal < AI_SHOOT_DISTANCE:
            self.kick_towards_goal(ball, target_goal, current_time)
            return
        
        if (teammate is not None and distance_to_goal > AI_SHOOT_DISTANCE 
            and self.is_closer_to_goal(teammate, target_goal)):
            self.pass_ball(ball, teammate, current_time)
            return

        self.move_towards(goal_x, goal_y, 0.8)

    
    def return_home(self):
        """Возвращает игрока на домашнюю позицию"""
        
        self.move_towards(self.home_x, self.home_y)
        

    def kick_towards_goal(self, ball, goal, current_time):
        """
        Выполняет удар AI-игрока по направлению к центру ворот
        
        Args:
            ball (Ball): Объект мяча
            goal (Goal): Ворота, по которым выполняется удар
            current_time (int): Текущее игровое время
        """
        
        target_x = goal.rect.centerx
        target_y = goal.rect.centery

        dx = target_x - ball.x
        dy = target_y - ball.y

        distance = math.hypot(dx, dy)

        if distance == 0:
            return

        # нормализация
        dx /= distance
        dy /= distance

        ball.vx = dx * KICK_FORCE
        ball.vy = dy * KICK_FORCE

        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = current_time

        
    def find_best_teammate(self, teammates, ball, enemies, target_goal):
        """
        Находит лучшего партнёра для паса на основе безопасности и выгодности передачи

        Args:
            teammates (list): Список партнёров по команде
            ball (Ball): Объект мяча
            enemies (list): Список игроков соперника
            target_goal (Goal): Ворота соперника
        
        Returns:
            AIPlayer | None: Лучший партнёр для паса или None,
            если подходящего игрока нет.
        """

        if teammates is None:
            teammates = []

        if enemies is None:
            enemies = []

        best_teammate = None
        best_score = -999999

        for teammate in teammates:
            
            if teammate == self:
                continue
            
            if not self.is_pass_safe(teammate, enemies):
                continue

            score = self.evaluate_pass(teammate, ball, enemies, target_goal)

            if score > best_score:
                best_score = score
                best_teammate = teammate

        return best_teammate
    

    def pass_ball(self, ball, teammate, current_time):
        """
        Выполняет пас AI-игрока выбранному партнёру
        
        Args:
            ball (Ball): Объект мяча
            teammate (AIPlayer): Партнёр, которому передаётся пас
            current_time (int): Текущее игровое время
        """

        dx = teammate.x - ball.x
        dy = teammate.y - ball.y

        distance = math.hypot(dx, dy)

        if distance == 0:
            return
        
        dx /= distance
        dy /= distance

        ball.vx = dx * PASS_FORCE
        ball.vy = dy * PASS_FORCE

        if ball.owner == self:
            ball.owner = None

        self.has_ball = False
        ball.last_owner = self
        ball.release_time = current_time


    def is_closest_to_ball(self, teammates, ball):
        """
        Проверяет, является ли игрок ближайшим к мячу среди партноеров
        
        Args:
            teammates (list): Список партнёров по команде
            ball (Ball): Объект мяча
        
        Returns:
            bool: True, если текущий игрок ближе всех к мячу, иначе False.
        """

        my_dist = math.hypot(self.x - ball.x, self.y - ball.y)

        for teammate in teammates:
            if teammate == self:
                continue
            
            teammate_dist = math.hypot(
                teammate.x - ball.x,
                teammate.y - ball.y
            )

            if teammate_dist < my_dist:
                return False

        return True


    def patrol_zone(self, ball):
        """
        Двигает игрока внутри защитной зоны в зависимости от положения мяча
        
        Args:
            ball (Ball): Объект мяча
        """
        
        if ball is None:
            return
        
        # смещение относительно мяча
        target_x = self.x
        target_y = self.y

        # если мяч в зоне - смещаемся к нему сбоку
        if self.zone_x_min < ball.x < self.zone_x_max:
            offset_y = 60 if self.role == 'DEFENDER' else -60

            target_x = ball.x
            target_y = ball.y + offset_y
        else:
            # возвращение в центр зоны
            target_x = (self.zone_x_min + self.zone_x_max) / 2
            target_y = (self.zone_y_min + self.zone_y_max) / 2

        self.move_towards(target_x, target_y, 0.7)


    def evaluate_pass(self, teammate, ball, enemies, target_goal):
        """
        Рассчитывает числовую оценку выгодности паса выбранному партнёру
        
        Args:
            teammate (AIPlayer): Партнёр, которому оценивается пас
            ball (Ball): Объект мяча
            enemies (list): Список игроков соперника
            target_goal (Goal): Ворота соперника
        
        Returns:
            float: Оценка выгодности паса
        """

        score = 0

        # Чем ближе партнёр к воротам соперника, тем лучше
        distance_to_goal = math.hypot(
            target_goal.rect.centerx - teammate.x,
            target_goal.rect.centery - teammate.y
        )
        score -= distance_to_goal * 1.5

        # Слишком дальний пас хуже
        pass_distance = math.hypot(teammate.x - ball.x, teammate.y - ball.y)
        score -= pass_distance * 0.4

        # Чем дальше ближайший соперник от партнёра, тем пас безопаснее
        if enemies:
            nearest_enemy = min(
                enemies,
                key=lambda e: math.hypot(e.x - teammate.x, e.y - teammate.y)
            )

            enemy_distance = math.hypot(
                nearest_enemy.x - teammate.x,
                nearest_enemy.y - teammate.y
            )
            score += enemy_distance * 3

        return score


    def is_pass_safe(self, teammate, enemies):
        """
        Проверяет, не находится ли соперник на линии паса
        
        Args:
            teammate (AIPlayer): Партнёр, которому планируется пас
            enemies (list): Список игроков соперника
        
        Returns:
            bool: True, если пас считается безопасным, иначе False
        """

        ax = self.x
        ay = self.y

        bx = teammate.x
        by = teammate.y

        for enemy in enemies:
            ex = enemy.x
            ey = enemy.y

            abx = bx - ax
            aby = by - ay

            aex = ex - ax
            aey = ey - ay

            ab_len_sq = abx * abx + aby * aby

            if ab_len_sq == 0:
                continue

            t = (aex * abx + aey * aby) / ab_len_sq
            t = max(0, min(1, t))

            closest_x = ax + abx * t
            closest_y = ay + aby * t

            dx = ex - closest_x
            dy = ey - closest_y

            distance = math.hypot(dx, dy)

            if distance < PASS_BLOCK_DISTANCE:
                return False

        return True


    def open_for_pass(self, ball, attack_goal, enemies):
        """
        Двигает игрока в свободную позицию впереди мяча для получения паса
        
        Args:
            ball (Ball): Объект мяча
            attack_goal (Goal): Ворота, в сторону которых идёт атака
            enemies (list): Список игроков соперника
        """

        if ball is None or attack_goal is None:
            return
        
        direction = 1 if attack_goal.rect.centerx > ball.x else -1

        target_x = ball.x + OPEN_PASS_DISTANCE * direction

        if self.home_y < HEIGHT // 2:
            target_y = ball.y - OPEN_PASS_Y_OFFSET
        else:
            target_y = ball.y + OPEN_PASS_Y_OFFSET

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.9)

    
    def cover(self, ball):
        """
        Двигает защитника в позицию страховки между домашней зоной и мячом
        
        Args:
            ball (Ball): Объект мяча
        """

        if ball is None:
            return

        # Защитник не летит к мячу, а держит позицию между своей зоной и мячом
        target_x = (self.home_x * DEFENDER_COVER_HOME_WEIGHT
                    + ball.x * DEFENDER_COVER_BALL_WEIGHT)
        target_y = (self.home_y * DEFENDER_COVER_HOME_WEIGHT
                    + ball.y * DEFENDER_COVER_BALL_WEIGHT)

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.6)


    def move_to_support_position(self, ball):
        """
        Двигает игрока в позицию поддержки рядом с атакой
        
        Args:
            ball (Ball): Объект мяча
        """

        if ball is None:
            return

        attack_direction = 1 if self.home_x < WIDTH // 2 else -1

        # Поддержка немного позади мяча
        target_x = ball.x - SUPPORT_DISTANCE_BEHIND_BALL * attack_direction
        target_y = self.home_y

        target_x = max(self.radius, min(WIDTH - self.radius, target_x))
        target_y = max(self.radius, min(HEIGHT - self.radius, target_y))

        self.move_towards(target_x, target_y, 0.7)


    def move_towards(self, target_x, target_y, speed_multiplier=1.0):
        """
        Двигает игрока к указанной точке с учётом множителя скорости
        
        Args:
            target_x (int | float): Координата цели по оси X
            target_y (int | float): Координата цели по оси Y
            speed_multiplier (int | float): Множитель скорости движения
        """

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.hypot(dx, dy)

        if distance == 0:
            return

        dx /= distance
        dy /= distance

        self.x += dx * self.speed * speed_multiplier * 0.85
        self.y += dy * self.speed * speed_multiplier * 0.85


    def is_closer_to_goal(self, teammate, goal):
        """
        Проверяет, находится ли партнёр ближе к воротам, чем текущий игрок
        
        Args:
            teammate (AIPlayer): Партнёр по команде
            goal (Goal): Ворота, расстояние до которых сравнивается
            Returns: bool: True, если партнёр ближе к воротам, иначе False
        """

        my_dist = math.hypot(goal.rect.centerx - self.x,
                             goal.rect.centery - self.y)
        teammate_dist = math.hypot(goal.rect.centerx - teammate.x,
                                   goal.rect.centery - teammate.y)
        
        return teammate_dist < my_dist
