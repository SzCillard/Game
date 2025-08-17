import math

import pygame

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((600, 600))
pygame.display.set_caption("Hex Map")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def draw_hexagon(surface, color, center, size):
    points = []
    for i in range(6):
        angle = math.radians(60 * i)
        x = center[0] + size * math.cos(angle)
        y = center[1] + size * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points, 1)


def draw_hex_map(surface, rows, cols, hex_size):
    for row in range(rows):
        for col in range(cols):
            x = col * hex_size * 1.5
            y = row * hex_size * math.sqrt(3) + (col % 2) * (
                hex_size * math.sqrt(3) / 2
            )
            draw_hexagon(surface, BLACK, (x + 50, y + 50), hex_size)


# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)
    draw_hex_map(screen, 10, 10, 30)
    pygame.display.flip()

pygame.quit()
