import os
import time
from abc import ABC, abstractmethod  # Import ABC module

import pygame

# --- Pygame Initialization ---
pygame.init()

# --- Constants ---
GRID_WIDTH = 10
GRID_HEIGHT = 10
CELL_SIZE = 70
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
messages = []


def add_message(text):
    messages.append((text, time.time()))


def draw_messages():
    y_offset = SCREEN_HEIGHT - 30
    current_time = time.time()
    messages[:] = [
        (msg, timestamp) for msg, timestamp in messages if current_time - timestamp < 3
    ]

    for msg, _ in reversed(messages):
        text_surface = font.render(msg, True, BLACK)
        screen.blit(text_surface, (10, y_offset))
        y_offset -= 25


# --- Helper Functions ---
def pixel_to_grid(px, py):
    return px // CELL_SIZE, py // CELL_SIZE


def grid_to_pixel(x, y):
    return x * CELL_SIZE, y * CELL_SIZE


def distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


# --- Load Images (Using Relative Paths) ---
BASE_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(BASE_DIR, "images")

SWORDSMAN_DIR = os.path.join(IMAGE_DIR, "swordsman")
ARCHER_DIR = os.path.join(IMAGE_DIR, "archer")

SWORDSMAN_PURPRLE_IMG = pygame.image.load(
    os.path.join(SWORDSMAN_DIR, "swordsman_purple.png")
)
SWORDSMAN_RED_IMG = pygame.image.load(os.path.join(SWORDSMAN_DIR, "swordsman_red.png"))

ARCHER_PURPLE_IMG = pygame.image.load(os.path.join(ARCHER_DIR, "archer_purple.png"))
ARCHER_RED_IMG = pygame.image.load(os.path.join(ARCHER_DIR, "archer_red.png"))

# Scale images to fit the grid cells
SWORDSMAN_PURPRLE_IMG = pygame.transform.scale(
    SWORDSMAN_PURPRLE_IMG, (CELL_SIZE, CELL_SIZE)
)
SWORDSMAN_RED_IMG = pygame.transform.scale
(SWORDSMAN_RED_IMG, (CELL_SIZE, CELL_SIZE))
ARCHER_PURPLE_IMG = pygame.transform.scale
(ARCHER_PURPLE_IMG, (CELL_SIZE, CELL_SIZE))
ARCHER_RED_IMG = pygame.transform.scale
(ARCHER_RED_IMG, (CELL_SIZE, CELL_SIZE))


# --- Abstract Unit Class ---
class Unit(ABC):
    def __init__(
        self, name, x, y, team, health, attack_power, attack_range, move_range, image
    ):
        self.name = name
        self.x = x
        self.y = y
        self.team = team
        self.health = health
        self.attack_power = attack_power
        self.attack_range = attack_range
        self.move_range = move_range
        self.has_acted = False
        self.image = image

    @abstractmethod
    def move(self, new_x, new_y, units):
        pass

    @abstractmethod
    def attack(self, target):
        pass

    def draw(self, screen):
        px, py = grid_to_pixel(self.x, self.y)
        screen.blit(self.image, (px, py))

        # Health display
        health_text = font.render(str(self.health), True, BLACK)
        screen.blit(health_text, (px + 5, py + 5))


# --- Soldier Classes ---
class Swordsman(Unit):
    def __init__(self, x, y, team, Image):
        super().__init__(
            "Swordsman",
            x,
            y,
            team,
            health=12,
            attack_power=4,
            attack_range=1,
            move_range=2,
            image=Image,
        )

    def move(self, new_x, new_y, units):
        if distance(self.x, self.y, new_x, new_y) <= self.move_range:
            if any(unit.x == new_x and unit.y == new_y for unit in units):
                add_message(f"{self.name} cannot move, tile occupied!")
                return
            self.x, self.y = new_x, new_y
            self.has_acted = True
        else:
            add_message(f"{self.name} can't move that far!")

    def attack(self, target):
        if distance(self.x, self.y, target.x, target.y) <= self.attack_range:
            target.health -= self.attack_power
            add_message(f"{self.name} attacked {target.name}, -{self.attack_power} HP!")
            self.has_acted = True
            if target.health <= 0:
                add_message(f"{target.name} was defeated!")
                return True
        else:
            add_message(f"{self.name} is too far to attack!")
        return False


class Archer(Unit):
    def __init__(self, x, y, team, Image):
        super().__init__(
            "Archer",
            x,
            y,
            team,
            health=8,
            attack_power=5,
            attack_range=3,
            move_range=3,
            image=Image,
        )

    def move(self, new_x, new_y, units):
        if distance(self.x, self.y, new_x, new_y) <= self.move_range:
            if any(unit.x == new_x and unit.y == new_y for unit in units):
                add_message(f"{self.name} cannot move, tile occupied!")
                return
            self.x, self.y = new_x, new_y
            self.has_acted = True
        else:
            add_message(f"{self.name} can't move that far!")

    def attack(self, target):
        if distance(self.x, self.y, target.x, target.y) <= self.attack_range:
            target.health -= self.attack_power
            add_message(f"{self.name} shot {target.name}, -{self.attack_power} HP!")
            self.has_acted = True
            if target.health <= 0:
                add_message(f"{target.name} was defeated!")
                return True
        else:
            add_message(f"{self.name} is too far to attack!")
        return False


# --- AI Class ---
class AI:
    def take_turn(self, units):
        ai_units = [unit for unit in units if unit.team == 2]
        player_units = [unit for unit in units if unit.team == 1]

        if not player_units:
            return

        for unit in ai_units:
            target = min(player_units, key=lambda p: distance(unit.x, unit.y, p.x, p.y))

            if distance(unit.x, unit.y, target.x, target.y) > unit.attack_range:
                dx = 1 if unit.x < target.x else -1 if unit.x > target.x else 0
                dy = 1 if unit.y < target.y else -1 if unit.y > target.y else 0
                unit.move(unit.x + dx, unit.y + dy, units)
            else:
                if unit.attack(target):
                    units.remove(target)


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

        for x in range(self.width):
            for y in range(self.height):
                px, py = grid_to_pixel(x, y)
                pygame.draw.rect(screen, GREEN, (px, py, CELL_SIZE, CELL_SIZE), 2)

        for unit in self.units:
            unit.draw(screen)


# --- Game Initialization ---
board = GridBoard(GRID_WIDTH, GRID_HEIGHT)

player_units = [
    Swordsman(2, 2, 1, SWORDSMAN_PURPRLE_IMG),
    Archer(3, 3, 1, ARCHER_PURPLE_IMG),
]
ai_units = [Swordsman(7, 7, 2, SWORDSMAN_RED_IMG), Archer(6, 6, 2, ARCHER_RED_IMG)]

for unit in player_units + ai_units:
    board.add_unit(unit)

enemy_bot = AI()

# --- Game Loop ---
running = True
selected_unit = None
player_turn = True

while running:
    screen.fill(WHITE)
    board.draw(screen)
    draw_messages()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            px, py = pygame.mouse.get_pos()
            x, y = pixel_to_grid(px, py)

            unit = board.get_unit_at(x, y)
            if unit and unit.team == 1 and not unit.has_acted:
                selected_unit = unit
            elif selected_unit and not unit:
                selected_unit.move(x, y, board.units)
                selected_unit = None
            elif selected_unit and unit and unit.team == 2:
                if selected_unit.attack(unit):
                    board.units.remove(unit)
                selected_unit = None

    if player_turn and all(unit.has_acted for unit in player_units):
        pygame.time.delay(500)
        enemy_bot.take_turn(board.units)

        for unit in player_units:
            unit.has_acted = False

        player_turn = True
        add_message("Player's turn!")
    pygame.display.flip()

pygame.quit()
