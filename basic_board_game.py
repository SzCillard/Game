import pygame
import random

# Constants
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 50
ROWS, COLS = HEIGHT // TILE_SIZE, WIDTH // TILE_SIZE
WHITE, BLACK, RED, GREEN, BLUE = (255,255,255), (0,0,0), (255,0,0), (0,255,0), (0,0,255)

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Strategy Game")
clock = pygame.time.Clock()

class Unit:
    def __init__(self, x, y, health, attack, move_range, color):
        self.x, self.y = x, y
        self.health, self.attack, self.move_range = health, attack, move_range
        self.color = color

    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS:
            self.x, self.y = new_x, new_y

    def attack_enemy(self, enemy):
        enemy.health -= self.attack
        if enemy.health <= 0:
            return True  # Enemy defeated
        return False

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(screen, WHITE, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)

# AI decision-making: move towards the closest player unit
class AI:
    def take_turn(self, ai_units, player_units):
        for unit in ai_units:
            if player_units:
                target = min(player_units, key=lambda p: abs(p.x - unit.x) + abs(p.y - unit.y))
                dx, dy = 0, 0
                if unit.x < target.x:
                    dx = 1
                elif unit.x > target.x:
                    dx = -1
                if unit.y < target.y:
                    dy = 1
                elif unit.y > target.y:
                    dy = -1
                unit.move(dx, dy)
                if unit.x == target.x and unit.y == target.y:
                    if unit.attack_enemy(target):
                        player_units.remove(target)  # Remove defeated player unit

# Initialize units
player_units = [Unit(2, 2, 10, 3, 2, GREEN), Unit(3, 3, 10, 2, 2, GREEN)]
ai_units = [Unit(10, 2, 8, 2, 2, RED), Unit(10, 4, 8, 2, 2, RED)]
ai = AI()

running, player_turn = True, True
selected_unit = None

while running:
    screen.fill(BLACK)
    for row in range(ROWS):
        for col in range(COLS):
            pygame.draw.rect(screen, WHITE, (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
    
    for unit in player_units + ai_units:
        unit.draw()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            mx, my = pygame.mouse.get_pos()
            tx, ty = mx // TILE_SIZE, my // TILE_SIZE
            for unit in player_units:
                if unit.x == tx and unit.y == ty:
                    selected_unit = unit
        elif event.type == pygame.KEYDOWN and selected_unit and player_turn:
            moves = {pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0)}
            if event.key in moves:
                dx, dy = moves[event.key]
                selected_unit.move(dx, dy)
            elif event.key == pygame.K_SPACE:
                for enemy in ai_units:
                    if selected_unit.x == enemy.x and selected_unit.y == enemy.y:
                        if selected_unit.attack_enemy(enemy):
                            ai_units.remove(enemy)  # Remove dead AI unit
            player_turn = False  # End player's turn
    
    if not player_turn:
        pygame.time.delay(500)
        ai.take_turn(ai_units, player_units)
        player_turn = True
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
