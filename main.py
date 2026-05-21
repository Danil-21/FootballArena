import pygame
import sys


WIDTH = 1200
HEIGHT = 700
FPS = 60

GREEN = (30, 160, 60)
WHITE = (255, 255, 255)
BLUE = (50, 80, 255)

PLAYER_RADIUS = 20
PLAYER_SPEED = 5

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Arena")

clock = pygame.time.Clock()


class Player:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED


    def move(self, keys):
        # По x
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        # По y
        if keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_s]:
            self.y += self.speed

    
    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (int(self.x), int(self.y)),
            self.radius
        )


def draw_field():
    """
    Рисует футбольное поле с разметкой
    """
    screen.fill(GREEN)

    # Центральная линия
    pygame.draw.line(screen, WHITE,
                     ((WIDTH // 2), 0),
                     (WIDTH // 2, HEIGHT), 
                     3
                     )
    
    # Центральный круг
    pygame.draw.circle(screen, WHITE,
                       (WIDTH // 2, HEIGHT // 2),
                       80, 
                       3
                       )
    

def main():
    running = True

    player = Player(WIDTH // 2, HEIGHT // 2, BLUE)

    while running:
        clock.tick(FPS)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Управление
        keys = pygame.key.get_pressed()
        player.move(keys)

        # Обновление (пусто)

        # Отрисовка
        draw_field()
        player.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
