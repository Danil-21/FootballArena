import pygame
import sys


WIDTH = 1200
HEIGHT = 700
FPS = 60

GREEN = (30, 160, 60)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Football Arena")

clock = pygame.time.Clock()


def draw_field():
    """
    Рисует футбольное поле с разметкой
    """
    screen.fill(GREEN)

    # Центральная линия
    pygame.draw.line(screen, WHITE,
                     ((WIDTH // 2), 0),
                     (WIDTH // 2, HEIGHT), 3)
    
    # Центральный круг
    pygame.draw.circle(screen, WHITE,
                       (WIDTH // 2, HEIGHT // 2),
                       80, 3)
    

def main():
    running = True

    while running:
        clock.tick(FPS)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Обновление (пусто)

        # Отрисовка
        draw_field()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
