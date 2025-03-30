import pygame
import time

# --- Pygame Initialization ---
pygame.init()

# --- Constants ---
GRID_WIDTH = 10
GRID_HEIGHT = 10
CELL_SIZE = 50
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Grid Strategy Game")

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
BLACK = (0, 0, 0)

# --- Pygame Font ---
pygame.font.init()
font = pygame.font.Font(None, 30)

# --- Message System ---
messages = []  # Stores (text, timestamp)

def add_message(text):
    """ Add a message with a timestamp. """
    messages.append((text, time.time()))

def draw_messages():
    """ Display messages at the bottom of the screen. """
    y_offset = SCREEN_HEIGHT - 30  # Start from bottom
    current_time = time.time()

    # Remove old messages (older than 3 seconds)
    messages[:] = [(msg, timestamp) for msg, timestamp in messages if current_time - timestamp < 3]

    for msg, _ in reversed(messages):  # Show latest messages at the bottom
        text_surface = font.render(msg, True, BLACK)
        screen.blit(text_surface, (10, y_offset))
        y_offset -= 25  # Move up for the next message


# --- Helper Functions ---
def pixel_to_grid(px, py):
    return px // CELL_SIZE, py // CELL_SIZE

def grid_to_pixel(x, y):
    return x * CELL_SIZE, y * CELL_SIZE

# --- Unit Class ---
class Unit:
    def __init__(self, name, x, y, team):
        self.name = name
        self.x = x
        self.y = y
        self.team = team  # 1 = Player, 2 = AI
        self.health = 10
        self.attack_power = 3
        self.move_range = 2
    
    def move(self, new_x, new_y):
        if abs(self.x - new_x) + abs(self.y - new_y) <= self.move_range:
            self.x, self.y = new_x, new_y

    def attack(self, target):
        target.health -= self.attack_power
        message = f"{self.name} attacked {target.name}, -{self.attack_power} HP!"
        add_message(message)

        if target.health <= 0:
            add_message(f"{target.name} was defeated!")
            return True  # Target is defeated
        return False

    def draw(self, screen):
        px, py = grid_to_pixel(self.x, self.y)
        color = BLUE if self.team == 1 else RED
        pygame.draw.circle(screen, color, (px + CELL_SIZE // 2, py + CELL_SIZE // 2), CELL_SIZE // 3)

        # Health display
        health_text = font.render(str(self.health), True, BLACK)
        screen.blit(health_text, (px + CELL_SIZE // 4, py + CELL_SIZE // 4))


# --- AI Class ---
class AI:
    def take_turn(self, units):
        ai_units = [unit for unit in units if unit.team == 2]
        player_units = [unit for unit in units if unit.team == 1]

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

                if abs(unit.x - target.x) + abs(unit.y - target.y) > 1:
                    unit.move(unit.x + dx, unit.y + dy)
                else:
                    if unit.attack(target):
                        units.remove(target)  # Remove defeated player unit


# --- Game Board ---
class GridBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.units = []

    def add_unit(self, unit):
        self.units.append(unit)

    def get_unit_at(self, x, y):
        for unit in self.units:
            if unit.x == x and unit.y == y:
                return unit
        return None

    def draw(self, screen):
        screen.fill(WHITE)

        # Draw grid
        for x in range(self.width):
            for y in range(self.height):
                px, py = grid_to_pixel(x, y)
                pygame.draw.rect(screen, GREEN, (px, py, CELL_SIZE, CELL_SIZE), 2)

        # Draw units
        for unit in self.units:
            unit.draw(screen)


# --- Game Initialization ---
board = GridBoard(GRID_WIDTH, GRID_HEIGHT)
player_unit = Unit("Swordsman", 2, 2, team=1)
ai_unit = Unit("Spearman", 7, 7, team=2)
board.add_unit(player_unit)
board.add_unit(ai_unit)
enemy_bot = AI()

# --- Game Loop ---
running = True
selected_unit = None
player_turn = True

while running:
    screen.fill(WHITE)
    board.draw(screen)
    draw_messages()  # Draw attack messages

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            px, py = pygame.mouse.get_pos()
            x, y = pixel_to_grid(px, py)

            unit = board.get_unit_at(x, y)
            if unit and unit.team == 1:  # Player selects a unit
                selected_unit = unit
            elif selected_unit and not unit:  # Move selected unit
                selected_unit.move(x, y)
                selected_unit = None
                player_turn = False
            elif selected_unit and unit and unit.team == 2:  # Attack
                if selected_unit.attack(unit):
                    board.units.remove(unit)
                selected_unit = None
                player_turn = False

    if not player_turn:
        pygame.time.delay(500)  # AI reaction delay
        enemy_bot.take_turn(board.units)
        player_turn = True

    pygame.display.flip()

pygame.quit()
